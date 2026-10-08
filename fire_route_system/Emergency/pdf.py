from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from django.http import HttpResponse
from django.utils import timezone
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.graphics.shapes import Drawing,PolyLine,Circle


def style():
    path=Path(__file__).parent/'fonts'/'NotoEmergency-Regular.ttf'
    if not path.exists():raise FileNotFoundError('Bundled Myanmar font is missing')
    if 'Myanmar' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Myanmar',str(path),shapable=True))
        pdfmetrics.registerFontFamily('Myanmar',normal='Myanmar',bold='Myanmar',italic='Myanmar',boldItalic='Myanmar')
    return ParagraphStyle('Myanmar',fontName='Myanmar',fontSize=10,leading=20,shaping=1)


class MyanmarParagraph(Paragraph):
    """Preserve logical Unicode alongside HarfBuzz's visually ordered glyphs."""
    def __init__(self,text,sty):
        self.logical_text=str(text)
        super().__init__(escape(self.logical_text).replace('\n','<br/>'),sty)

    def draw(self):
        actual_text=(b'\xfe\xff'+self.logical_text.encode('utf-16-be')).hex()
        self.canv.addLiteral('/Span << /ActualText <'+actual_text+'> >> BDC')
        try:super().draw()
        finally:self.canv.addLiteral('EMC')


def paragraph(text,sty):return MyanmarParagraph(text,sty)


def response(story,filename):
    buffer=BytesIO();SimpleDocTemplate(buffer,title='မီးဘေးအရေးပေါ်စနစ်',author='Fire Emergency Demo').build(story)
    result=HttpResponse(buffer.getvalue(),content_type='application/pdf');result['Content-Disposition']=f'attachment; filename="{filename}"';return result


def route_diagram(coordinates):
    drawing=Drawing(460,260)
    minlat,maxlat=min(p[0] for p in coordinates),max(p[0] for p in coordinates)
    minlon,maxlon=min(p[1] for p in coordinates),max(p[1] for p in coordinates)
    scale=min(420/max(maxlon-minlon,0.00001),220/max(maxlat-minlat,0.00001))
    points=[(20+(p[1]-minlon)*scale,20+(p[0]-minlat)*scale) for p in coordinates]
    if len(points)>1:drawing.add(PolyLine([v for p in points for v in p],strokeColor=colors.HexColor('#a42635'),strokeWidth=2))
    drawing.add(Circle(*points[0],4,fillColor=colors.blue));drawing.add(Circle(*points[-1],4,fillColor=colors.red))
    return drawing


def incident_pdf_response(request,incident):
    from .permissions import managed_station_ids
    sty=style();story=[paragraph(f'မီးလောင်ဖြစ်စဉ် {incident.pk}',sty),paragraph(f'{incident.address or "GPS နေရာ"} / {incident.scale_display} / {incident.status_display}',sty)]
    deployments=incident.deployments.select_related('station')
    if not request.user.is_admin:deployments=deployments.filter(station_id__in=managed_station_ids(request.user)+[request.user.station_id])
    for deployment in deployments:
        story.append(paragraph(deployment.station.name,sty))
        story.append(paragraph('ယာဉ်များ: '+', '.join(deployment.vehicles.values_list('vehicle__registration',flat=True)),sty))
        story.append(paragraph('အမှန်တကယ်လိုက်ပါဝန်ထမ်း: '+', '.join((p.employee.full_name or p.employee.username) for p in deployment.personnel.filter(actual=True).select_related('employee')),sty))
        route=deployment.route
        if route.get('error'):story.append(paragraph(route['error'],sty))
        if route.get('coordinates'):
            story.append(route_diagram(route['coordinates']))
            story.append(paragraph(f'လမ်းကွန်ရက်ပေါ်အကွာအဝေး {route["metres"]} m · © OpenStreetMap contributors',sty))
            for step in route['instructions']:story.append(paragraph(f'{step["turn"]} / {step["road"]} / {step["direction"]} / {step["metres"]} m',sty))
    if request.user.is_admin or incident.lead_station_id in managed_station_ids(request.user):
        try:final=incident.final_report
        except Exception:final=None
        if final:
            story.extend([paragraph('နောက်ဆုံးအစီရင်ခံစာ',sty),paragraph(final.narrative,sty),paragraph(f'ရေဂါလန်စုစုပေါင်း {final.snapshot.get("water_gallons",0)}',sty)])
    return response(story,f'incident-{incident.pk}.pdf')


def report_pdf(request,query):
    sty=style();story=[paragraph('မီးလောင်ဖြစ်စဉ် အစီရင်ခံစာ',sty)]
    for incident in query:
        story.extend([paragraph(f'{incident.pk} / {timezone.localtime(incident.reported_at):%d-%m-%Y %I:%M %p} / {incident.scale_display} / {incident.status_display}',sty),paragraph(incident.address or 'GPS နေရာ',sty),Spacer(1,10)])
    return response(story,'incidents.pdf')
