import SwiftUI

// Visualize AI body scan. Compiles to nothing until the Visualize Swift package is added
// (Xcode > File > Add Package Dependencies, URL from the Visualize portal), and only shows
// on iPhones with a TrueDepth camera.
#if canImport(Visualize)
import UIKit
import Visualize

struct BodyScanButton: View {
    @Environment(AppStore.self) private var store
    @State private var supported = false
    @State private var scanning = false

    var body: some View {
        Group {
            if supported {
                Button { Task { await scan() } } label: {
                    HStack {
                        Image(systemName: "figure.arms.open")
                        Text(scanning ? "Scanning…" : "Body scan").font(Theme.text(15, .semibold))
                        Spacer()
                        Text("Body fat %").font(Theme.text(12.5)).foregroundStyle(Theme.secondary)
                    }
                    .frame(minHeight: 44)
                }
                .buttonStyle(.plain)
                .disabled(scanning)
                .card(18, padding: 14)
            }
        }
        .task { supported = await Visualize.isDeviceSupported }
    }

    private func scan() async {
        guard let p = store.profile, let cm = p.heightCm, let kg = p.weightKg, let age = p.age,
              let vc = UIApplication.shared.connectedScenes
                .compactMap({ ($0 as? UIWindowScene)?.keyWindow?.rootViewController }).first
        else { store.error = "Add height, weight and age first."; return }
        var top = vc
        while let presented = top.presentedViewController { top = presented }

        scanning = true
        defer { scanning = false }
        do {
            // TODO(visualize): if the SDK needs the publishable key set up front, do it here
            // with Config.visualizePublishableKey (exact call is in the portal docs).
            let token = try await store.visualizeSessionToken()
            let subject = ScanSubject(gender: p.sex == "female" ? .female : .male,
                                      heightIn: cm / 2.54, weightLb: kg * 2.20462, ageYears: age)
            let result = try await Visualize.startScan(sessionToken: token, subject: subject, presentingFrom: top)
            await store.saveBodyScan(bodyFatPercent: result.measurements.bodyFatPercent)
        } catch {
            store.error = error.localizedDescription
        }
    }
}
#else
struct BodyScanButton: View {
    var body: some View { EmptyView() }
}
#endif
