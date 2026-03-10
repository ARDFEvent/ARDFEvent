import multiprocessing
import platform

import webview

try:
    multiprocessing.set_start_method('spawn', force=True)
except RuntimeError:
    pass


def launch_webview_process(html, title):
    class LocalApi:
        def __init__(self, content):
            self.content = content

        def export_html(self):
            active_win = webview.active_window()
            res = active_win.create_file_dialog(webview.FileDialog.SAVE, save_filename="report.html")
            if res:
                with open(res, 'w', encoding='utf-8') as f:
                    f.write(self.content)

    api = LocalApi(html)

    toolbar_html = """
    <div id="p-toolbar" style="position:fixed; top:0; left:0; right:0; background:#e1e1e1; 
         padding:10px; border-bottom:1px solid #999; z-index:9999; display:flex; gap:10px;">
        <button onclick="window.print()" style="padding:5px 15px; cursor:pointer;">Vytisknout</button>
        <button onclick="window.pywebview.api.export_html()" style="padding:5px 15px; cursor:pointer;">Exportovat HTML</button>
    </div>
    <style>
        body { padding-top: 50px !important; }
        @media print { #p-toolbar { display: none !important; } body { padding-top: 0 !important; } }
    </style>
    """

    if "<body>" in html:
        final_html = html.replace("<body>", f"<body>{toolbar_html}")
    else:
        final_html = toolbar_html + html

    window = webview.create_window(title, html=final_html, js_api=api)
    webview.start(gui=('gtk' if platform.system().lower() == "linux" else None))


class PreviewWindow:
    def __init__(self, html):
        p = multiprocessing.Process(
            target=launch_webview_process,
            args=(html, "Náhled"),
        )
        p.daemon = True
        p.start()
