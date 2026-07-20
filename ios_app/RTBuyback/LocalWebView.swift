import SwiftUI
import WebKit
import UIKit

struct LocalWebView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator {
        Coordinator(self)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.preferences.setValue(true, forKey: "allowFileAccessFromFileURLs")
        config.setValue(true, forKey: "allowUniversalAccessFromFileURLs")

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.isOpaque = false
        webView.backgroundColor = UIColor(red: 9/255, green: 14/255, blue: 26/255, alpha: 1.0)
        webView.scrollView.bounces = true

        loadLocalHTML(into: webView)
        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    private func loadLocalHTML(into webView: WKWebView) {
        if let wwwPath = Bundle.main.path(forResource: "www", ofType: nil) {
            let wwwURL = URL(fileURLWithPath: wwwPath)
            let indexURL = wwwURL.appendingPathComponent("index.html")
            webView.loadFileURL(indexURL, allowingReadAccessTo: wwwURL)
        } else if let indexURL = Bundle.main.url(forResource: "index", withExtension: "html") {
            let bundleURL = Bundle.main.bundleURL
            webView.loadFileURL(indexURL, allowingReadAccessTo: bundleURL)
        }
    }

    class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        var parent: LocalWebView

        init(_ parent: LocalWebView) {
            self.parent = parent
        }

        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if let url = navigationAction.request.url {
                let scheme = url.scheme?.lowercased() ?? ""
                if scheme == "whatsapp" || scheme == "tel" || scheme == "mailto" || (scheme == "https" && url.host?.contains("wa.me") == true) {
                    UIApplication.shared.open(url, options: [:], completionHandler: nil)
                    decisionHandler(.cancel)
                    return
                }
            }
            decisionHandler(.allow)
        }

        func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration, for navigationAction: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
            if navigationAction.targetFrame == nil || !(navigationAction.targetFrame?.isMainFrame ?? false) {
                if let url = navigationAction.request.url {
                    UIApplication.shared.open(url, options: [:], completionHandler: nil)
                }
            }
            return nil
        }
    }
}
