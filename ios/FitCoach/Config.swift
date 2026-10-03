import Foundation

enum Config {
    // Simulator reaches the Mac via localhost. A real iPhone needs the Mac's LAN IP
    // (`ipconfig getifaddr en0`, same Wi-Fi) or an HTTPS tunnel URL.
    #if targetEnvironment(simulator)
    static let baseURL = URL(string: "http://localhost:8000")!
    #else
    static let baseURL = URL(string: "https://finest-game-domain-scotland.trycloudflare.com")! // ponytail: cloudflared quick tunnel, URL changes on restart
    #endif
    // true = no backend needed; MockAPIClient serves the seed data from SPEC §2.4.
    static let useMock = false
}
