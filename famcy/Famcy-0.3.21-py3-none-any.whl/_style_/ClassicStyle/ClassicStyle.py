import Famcy
from flask import render_template

class ClassicStyle(Famcy.FamcyStyle):
	def __init__(self):
		super(ClassicStyle, self).__init__()

		# set default value
		self.title = ""
		self.desc = ""
		self.font_theme = Famcy.FamcyFontTheme()
		self.loader = Famcy.FamcyStyleLoader()
		self.color_theme = Famcy.FamcyColorTheme()

		self.side_bar = Famcy.FamcyStyleSideBar()
		self.nav_bar = Famcy.FamcyStyleNavBar()

	def setHeadScript(self, title=None, desc=None):
		if title:
			self.title = title
		if desc:
			self.desc = desc

	def render(self, extra_script, content, background_flag=False, route="", time=5000, form_init_js=None, end_script="", **kwargs):

		html_header = self.setDashboardHTMLHeader()
		end_js = end_script+self.setDashboardJavaScript()
		color_theme = self.color_theme.render()
		font_theme = self.font_theme.render()
		load_spinner = self.loader.render()

		side_bar = self.side_bar.render()
		nav_bar = self.nav_bar.render()

		body_on_load = "background_loop('" + self.main_url + str(route) + "/bgloop" + "', '" + str(route) + "', " + str(time) + ");console.log('start!')" if background_flag else ""
		if kwargs["event_source_flag"]:
			_event_source_script = '''
			var source = new EventSource('%s');
		    source.addEventListener('publish', function(event) {
		        var data = JSON.parse(event.data);
		        update_event_source_target(data)
		    }, false);
		    source.addEventListener('error', function(event) {
		        console.log("Error"+ event)
		    }, false);
			''' % (str(self.main_url)+str(route)+"/event_source")
		else:
			_event_source_script = ''
			
		return render_template("index.html", event_source=_event_source_script, font_theme=font_theme, form_init_js=form_init_js, load_spinner=load_spinner, color_theme=color_theme, html_header=html_header, side_bar=side_bar, nav_bar=nav_bar, content=content, extra_script=extra_script, end_js=end_js, body_on_load=body_on_load)
