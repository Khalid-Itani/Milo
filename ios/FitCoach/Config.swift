import Foundation

enum Config {
    // Simulator can reach the Mac via localhost. A real device needs the Mac's LAN IP
    // (e.g. http://192.168.1.20:8000) or an ngrok URL.
    static let baseURL = URL(string: "http://localhost:8000")!
    // true = no backend needed; MockAPIClient serves the seed data from SPEC §2.4.
    static let useMock = false
}
