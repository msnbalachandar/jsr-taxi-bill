import os
import json
import tempfile
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle

from reportlab.lib.pagesizes import A5
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class SignaturePad(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.has_signature = False
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.96, 0.96, 0.96, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(0.7, 0.7, 0.7, 1)
            Line(rectangle=(self.x, self.y, self.width, self.height), width=1)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(0.05, 0.1, 0.3, 1)
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=1.6)
            self.has_signature = True
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if 'line' in touch.ud and self.collide_point(*touch.pos):
            touch.ud['line'].points += [touch.x, touch.y]
            return True
        return super().on_touch_move(touch)

    def clear(self):
        self.canvas.clear()
        self._update_bg()
        self.has_signature = False


class TaxiBillApp(App):
    VALIDITY_DAYS = 365

    def check_license_validity(self):
        license_path = os.path.join(self.user_data_dir, "app_license.json")
        now = datetime.now()

        if not os.path.exists(license_path):
            license_data = {
                "install_date": now.strftime("%Y-%m-%d"),
                "last_run_date": now.strftime("%Y-%m-%d")
            }
            try:
                with open(license_path, "w") as f:
                    json.dump(license_data, f)
            except Exception as e:
                return True, f"License check bypassed: {e}", self.VALIDITY_DAYS

            return True, "Valid", self.VALIDITY_DAYS

        try:
            with open(license_path, "r") as f:
                license_data = json.load(f)

            install_date = datetime.strptime(license_data["install_date"], "%Y-%m-%d")
            last_run = datetime.strptime(license_data.get("last_run_date", license_data["install_date"]), "%Y-%m-%d")

            if now < last_run:
                return False, "Clock tampering detected. Please set accurate date and time.", 0

            expiry_date = install_date + timedelta(days=self.VALIDITY_DAYS)
            remaining_days = (expiry_date - now).days

            if remaining_days <= 0:
                return False, "Your 1-year app validity has expired.", 0

            license_data["last_run_date"] = now.strftime("%Y-%m-%d")
            with open(license_path, "w") as f:
                json.dump(license_data, f)

            return True, "Valid", remaining_days

        except Exception as e:
            return False, f"License verification error: {str(e)}", 0

    def build(self):
        self.title = "JSR Taxi Bill Generator"

        is_valid, msg, days_left = self.check_license_validity()

        if not is_valid:
            lock_box = BoxLayout(orientation='vertical', padding=30, spacing=15)
            lock_box.add_widget(Label(
                text="[color=ff4444][b]LICENSE EXPIRED[/b][/color]",
                markup=True,
                font_size='24sp',
                halign='center'
            ))
            lock_box.add_widget(Label(
                text=f"{msg}\n\nPlease contact support to renew your license.",
                halign='center',
                font_size='15sp'
            ))
            return lock_box

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=20)
        layout.bind(minimum_height=layout.setter('height'))

        layout.add_widget(
            Label(
                text="[b]JSR Taxi Bill Generator[/b]",
                markup=True,
                font_size='22sp',
                size_hint_y=None,
                height=40,
            )
        )
        layout.add_widget(
            Label(
                text=f"[color=88cc88]License Active: {days_left} days remaining[/color]",
                markup=True,
                font_size='13sp',
                size_hint_y=None,
                height=25,
            )
        )

        self.inputs = {}
        fields = [
            ("logo_file", "Logo File Path (optional, defaults to logo.png)"),
            ("bill_no", "Bill No."),
            ("bill_date", "Bill Date (DD/MM/YY)"),
            ("passenger_name", "Passenger Name"),
            ("client_company", "Company Name"),
            ("passenger_address", "Passenger Address"),
            ("car_type", "Car Type (e.g. Sedan/SUV)"),
            ("car_no", "Car No."),
            ("opp_date", "Opening Date"),
            ("close_date", "Closing Date"),
            ("opp_time", "Opening Time"),
            ("close_time", "Closing Time"),
            ("opp_mr", "Opening Meter Reading"),
            ("close_mr", "Closing Meter Reading"),
            ("per_km_rate", "Rate per KM (Rs.)"),
            ("extra_km", "Extra K.M."),
            ("extra_hrs", "Extra Hrs."),
            ("dry_night_charge", "Dry Night Charge"),
            ("toll_tax", "Toll & Tax"),
            ("parking_charge", "Parking Charge"),
            ("advance", "Advance Amount"),
            ("s_tax", "Service Tax"),
        ]

        today = datetime.today().strftime("%d/%m/%y")

        for key, label_text in fields:
            lbl = Label(text=label_text, size_hint_y=None, height=26, halign='left')
            lbl.bind(size=lbl.setter('text_size'))
            layout.add_widget(lbl)

            inp = TextInput(multiline=False, size_hint_y=None, height=38)
            if key == 'bill_date':
                inp.text = today
            elif key == 'logo_file':
                inp.text = "logo.png"
            self.inputs[key] = inp
            layout.add_widget(inp)

        # Signature Section
        layout.add_widget(Label(text="[b]Driver Signature[/b] (Draw below)", markup=True, size_hint_y=None, height=30))
        self.driver_pad = SignaturePad(size_hint_y=None, height=110)
        layout.add_widget(self.driver_pad)

        btn_clear_driver = Button(text="Clear Driver Signature", size_hint_y=None, height=32)
        btn_clear_driver.bind(on_press=lambda inst: self.driver_pad.clear())
        layout.add_widget(btn_clear_driver)

        layout.add_widget(Label(text="[b]Customer Signature[/b] (Draw below)", markup=True, size_hint_y=None, height=30))
        self.cust_pad = SignaturePad(size_hint_y=None, height=110)
        layout.add_widget(self.cust_pad)

        btn_clear_cust = Button(text="Clear Customer Signature", size_hint_y=None, height=32)
        btn_clear_cust.bind(on_press=lambda inst: self.cust_pad.clear())
        layout.add_widget(btn_clear_cust)

        # Generate Button
        btn_gen = Button(
            text="Generate PDF Bill",
            size_hint_y=None,
            height=50,
            background_color=(0.15, 0.55, 0.95, 1),
        )
        btn_gen.bind(on_press=self.generate_pdf)
        layout.add_widget(btn_gen)

        self.status_label = Label(text="", size_hint_y=None, height=45)
        layout.add_widget(self.status_label)

        scroll.add_widget(layout)
        return scroll

    def generate_pdf(self, instance):
        is_valid, msg, _ = self.check_license_validity()
        if not is_valid:
            self.status_label.text = "Error: App license has expired."
            return

        temp_files = []
        try:
            data = {k: v.text.strip() for k, v in self.inputs.items()}

            def get_val(k):
                try:
                    return float(data[k])
                except (ValueError, TypeError, KeyError):
                    return 0.0

            opp = get_val('opp_mr')
            close = get_val('close_mr')
            running_km = max(0.0, close - opp)
            rate = get_val('per_km_rate')
            base_amount = running_km * rate

            toll_tax = get_val('toll_tax')
            parking = get_val('parking_charge')
            dry_night = get_val('dry_night_charge')
            advance = get_val('advance')
            stax = get_val('s_tax')

            subtotal = base_amount + toll_tax + parking + dry_night
            grand_total = subtotal + stax - advance

            user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            if os.path.exists("/sdcard/Download"):
                output_dir = "/sdcard/Download"
            elif os.path.exists(user_downloads):
                output_dir = user_downloads
            else:
                output_dir = "."

            bill_num = data.get('bill_no') or "1"
            file_path = os.path.join(output_dir, f"Bill_{bill_num}.pdf")

            doc = SimpleDocTemplate(
                file_path,
                pagesize=A5,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30,
            )
            styles = getSampleStyleSheet()

            company_title_style = ParagraphStyle(
                'CompanyTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=1, spaceAfter=2
            )
            header_style = ParagraphStyle(
                'HeaderStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, alignment=1, spaceAfter=6
            )
            bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5)
            text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=11)
            center_label_style = ParagraphStyle('CenterLabel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, alignment=1)

            story = []

            custom_logo = data.get('logo_file', '').strip()
            logo_path = custom_logo if (custom_logo and os.path.exists(custom_logo)) else "logo.png"

            if os.path.exists(logo_path):
                img = RLImage(logo_path, width=80, height=45)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 3))

            story.extend([
                Paragraph("JSR Travels and Call Drivers", company_title_style),
                Paragraph("Perumbakkam, Chennai - 60010
