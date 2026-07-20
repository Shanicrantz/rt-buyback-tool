import SwiftUI

struct ContentView: View {
    var body: some View {
        ZStack {
            Color(red: 9/255, green: 14/255, blue: 26/255)
                .ignoresSafeArea()
            
            LocalWebView()
                .ignoresSafeArea(.keyboard, edges: .bottom)
        }
    }
}

#Preview {
    ContentView()
}
