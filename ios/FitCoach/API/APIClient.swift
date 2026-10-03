import Foundation

struct APIError: LocalizedError {
    var status: Int
    var body: String
    var errorDescription: String? { "HTTP \(status): \(body.prefix(200))" }
}

actor APIClient {
    static let shared = APIClient()

    private let decoder: JSONDecoder = { let d = JSONDecoder(); d.keyDecodingStrategy = .convertFromSnakeCase; return d }()
    private let encoder: JSONEncoder = { let e = JSONEncoder(); e.keyEncodingStrategy = .convertToSnakeCase; return e }()

    func get<T: Decodable>(_ path: String) async throws -> T { try await send("GET", path, nil) }
    func post<T: Decodable>(_ path: String, _ body: (any Encodable)? = nil) async throws -> T { try await send("POST", path, body) }
    func patch<T: Decodable>(_ path: String, _ body: any Encodable) async throws -> T { try await send("PATCH", path, body) }
    func delete(_ path: String) async throws { let _: OK = try await send("DELETE", path, nil) }

    private func send<T: Decodable>(_ method: String, _ path: String, _ body: (any Encodable)?) async throws -> T {
        let bodyData = try body.map { try encoder.encode($0) }
        if Config.useMock {
            return try decoder.decode(T.self, from: MockAPIClient.respond(method, path, bodyData))
        }
        var req = URLRequest(url: URL(string: path, relativeTo: Config.baseURL)!)
        req.httpMethod = method
        req.timeoutInterval = 300 // /chat runs a multi-step LLM tool loop
        req.setValue("Bearer \(Secrets.demoAPIToken)", forHTTPHeaderField: "Authorization")
        if method != "GET" {
            // Same key on every retry below, so the backend replays instead of saving twice.
            req.setValue(UUID().uuidString, forHTTPHeaderField: "Idempotency-Key")
        }
        if let bodyData {
            req.httpBody = bodyData
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        }
        // Retry brief outages (tunnel reconnects return 502/503/504/52x; dropped connections throw).
        var attempt = 0
        while true {
            attempt += 1
            do {
                let (data, resp) = try await URLSession.shared.data(for: req)
                let status = (resp as? HTTPURLResponse)?.statusCode ?? 0
                if (200..<300).contains(status) { return try decoder.decode(T.self, from: data) }
                let error = APIError(status: status, body: String(decoding: data, as: UTF8.self))
                guard [502, 503, 504, 520, 521, 522, 523, 524, 530].contains(status), attempt < 4 else { throw error }
            } catch let e as URLError where e.code != .cancelled && attempt < 4 {
                // fall through to retry
            }
            try await Task.sleep(for: .seconds(Double(attempt) * 1.5))
        }
    }
}
