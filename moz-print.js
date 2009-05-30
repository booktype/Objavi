/* To omit typing "-printmode PDF" */
user_pref("extensions.cmdlnprint.mode", 1);

/* fake printer "drupal pdf dummy" */
user_pref("print.printer_objavi.print_downloadfonts", true);
user_pref("print.printer_objavi.print_edge_bottom", 0);
user_pref("print.printer_objavi.print_edge_left", 0);
user_pref("print.printer_objavi.print_edge_right", 0);
user_pref("print.printer_objavi.print_edge_top", 0);
user_pref("print.printer_objavi.print_in_color", true);

user_pref("print.printer_objavi.print_bgcolor", true);
user_pref("print.printer_objavi.print_bgimages", true);

/* Note that margins are string, while unwritable margins are integer. */
user_pref("print.printer_objavi.print_margin_top", "0.5");
user_pref("print.printer_objavi.print_margin_bottom", "0.5");
user_pref("print.printer_objavi.print_margin_left", "0.5");
user_pref("print.printer_objavi.print_margin_right", "0.5");

user_pref("print.printer_objavi.print_unwritable_margin_top", 0);
user_pref("print.printer_objavi.print_unwritable_margin_bottom", 0);
user_pref("print.printer_objavi.print_unwritable_margin_left", 0);
user_pref("print.printer_objavi.print_unwritable_margin_right", 0);

user_pref("print.printer_objavi.print_headercenter", "");
user_pref("print.printer_objavi.print_headerleft", "&T");
user_pref("print.printer_objavi.print_headerright", "");

user_pref("print.printer_objavi.print_footercenter", "");
user_pref("print.printer_objavi.print_footerleft", "&U");
user_pref("print.printer_objavi.print_footerright", "");

/* paperWidth is also string, as it stands for float (or double). */
user_pref("print.printer_objavi.print_paper_width", "280");

user_pref("browser.sessionstore.resume_from_crash", false);

//Commands to input:
//>firefox -print artisan.karma-lab.net/print/1711 -printprinter "drupal pdf dummy"