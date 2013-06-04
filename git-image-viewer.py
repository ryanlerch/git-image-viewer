
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio
import sys
import os
import subprocess


cachedir = "cache/"

class ImageVersionsWindow(Gtk.ApplicationWindow):
    def __init__(self, app, activefilename):
        Gtk.Window.__init__(self, title="Git Images", application=app)
        self.activefilename = activefilename
        # Set Dark Theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        
        self.set_wmclass("Git Images", "Git Images")
        self.set_default_size(800, 600)
        self.set_hide_titlebar_when_maximized(True)
        
        
        myprovider = Gtk.CssProvider()
        myprovider.load_from_path('style.css')
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(),myprovider,600)
        
        self.image = Gtk.Image()
        
        self.treestore = Gtk.TreeStore(str,str)
        self.treeview = Gtk.TreeView(self.treestore)
        self.treeview.set_show_expanders(0)
        self.treeview.set_level_indentation(5)
        self.treeview.set_headers_visible(False)
        self.tvcolumn = Gtk.TreeViewColumn('Column 0')
        self.treeview.append_column(self.tvcolumn)
        self.cell = Gtk.CellRendererText()
        self.cell.set_padding(20,0)
        self.tvcolumn.pack_start(self.cell, True)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        hpane = Gtk.HPaned()
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_policy(2,1)
        scrolledwindow.add(self.treeview)
        hpane.add1(scrolledwindow)
        hpane.add2(self.image)
        self.add(hpane)
        self.show_all()
        
        self.generate(activefilename)
        handler_id = self.treeview.get_selection().connect("changed", self.cb_treeviewchanged)
    
    def cb_treeviewchanged(self, clickedTreeview):
        (model, iter) = clickedTreeview.get_selected()
        if iter != None:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(cachedir+model[iter][1])
                self.image.set_from_pixbuf(pixbuf)
            except GLib.GError:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file("images/missing.svg")
                self.image.set_from_pixbuf(pixbuf)
    
    def generate(self, thefile):
        self.treestore.clear()
        filepath = os.path.dirname(thefile)
        filename = os.path.basename(thefile)
        p = subprocess.Popen(["git", "--no-pager","log","--pretty=%H	%ar",filepath+"/"+filename], cwd=filepath, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        out, err = p.communicate()
        p2 = subprocess.Popen(["git", "rev-parse","--show-toplevel"], cwd=filepath, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        gitroot =  p2.communicate()[0].strip()
        print os.path.relpath(thefile,gitroot)
        lines = out.split("\n")
        lines.pop()
        generatePNGS = subprocess.Popen(["inkscape","--shell"], cwd=cachedir, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in lines:
            data = i.split("\t")
            piter = self.treestore.append(None, [data[1], data[0]])
            try:
                open(cachedir+data[0])
            except IOError:
                f = open(cachedir+"svg/"+data[0]+".svg", 'w+')
                generateSVGprocess = subprocess.Popen(["git", "--no-pager","show",data[0]+":"+os.path.relpath(thefile,gitroot)], cwd=gitroot, stdout=f)
                f.close()
                generateSVGprocess.communicate()
                generatePNGS.stdin.write("--export-png="+data[0]+" -D svg/"+data[0]+".svg\n")
        generatePNGS.stdin.write("\n")
        inkscapeoutput = generatePNGS.communicate()
        self.treeview.set_cursor(0)
        self.cb_treeviewchanged(self.treeview.get_selection())

class ImageVersionsApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self, 
                                application_id="org.gtk.ImageVersions",
                                flags=Gio.ApplicationFlags.HANDLES_OPEN,
                                register_session=True)
        
    def do_open(self, files, n_files, hint):
        # ([], 1) for 1 argument, ([], 2) for 2 arguments, etc. 
        # files is always empty.
        self.win = ImageVersionsWindow(self,files[0].get_path())
        self.win.show_all()

    def do_activate(self):
        self.win = ImageVersionsWindow(self)
        self.win.show_all()
        

    def do_startup(self):
        # start the application
        Gtk.Application.do_startup(self)

        # create a menu
        menu = Gio.Menu()
        menu.append("Reload", "app.reload")
        menu.append("Quit", "app.quit")
        self.set_app_menu(menu)

        reload_action = Gio.SimpleAction.new("reload", None)
        reload_action.connect("activate", self.reload_cb)
        self.add_action(reload_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.quit_cb)
        self.add_action(quit_action)

    def reload_cb(self, action, parameter):
        self.win.generate(self.win.activefilename)

    def quit_cb(self, action, parameter):
        print "You have quit."
        self.quit()

app = ImageVersionsApplication()
exit_status = app.run(sys.argv)
sys.exit(exit_status)
