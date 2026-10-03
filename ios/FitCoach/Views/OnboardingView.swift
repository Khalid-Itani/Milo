import SwiftUI

/// First-launch sheet (shown when /profile has no height); also opened from the Today avatar.
struct OnboardingView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State private var height = ""
    @State private var weight = ""
    @State private var age = ""
    @State private var sex = "male"
    @State private var saving = false
    @State private var result: User?

    private var input: ProfileInput? {
        guard let h = Double(height.replacingOccurrences(of: ",", with: ".")), (100...250).contains(h),
              let w = Double(weight.replacingOccurrences(of: ",", with: ".")), (25...350).contains(w),
              let a = Int(age), (10...110).contains(a) else { return nil }
        return ProfileInput(heightCm: h, weightKg: w, age: a, sex: sex)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            VStack(alignment: .leading, spacing: 4) {
                ScreenTitle(title: result == nil ? "About you" : "You’re set", size: 28)
                Text(result == nil ? "Milo uses this to set your calorie and macro targets." : "Here’s where you start.")
                    .font(Theme.text(14)).foregroundStyle(Theme.secondary)
            }
            .padding(.top, 24)

            if let u = result {
                VStack(alignment: .leading, spacing: 6) {
                    Text("BMI").font(Theme.text(12.5, .medium)).foregroundStyle(Theme.secondary)
                    HStack(alignment: .firstTextBaseline, spacing: 8) {
                        Text(u.bmi.map(fmt) ?? "—").font(Theme.mono(34)).tracking(-1.2)
                        Text(u.bmiCategory ?? "").font(Theme.text(15, .semibold))
                    }
                    if let k = u.kcalTarget {
                        Text("Daily target \(fmt(k)) kcal · \(fmt(u.proteinG ?? 0)) g protein")
                            .font(Theme.text(12.5)).foregroundStyle(Theme.secondary)
                    }
                }
                .card(22)
                Spacer()
                Button("Done") { dismiss() }.buttonStyle(BigButtonStyle())
            } else {
                VStack(spacing: 0) {
                    row("Height", "cm", $height, .decimalPad)
                    Divider().overlay(Theme.hairline)
                    row("Weight", "kg", $weight, .decimalPad)
                    Divider().overlay(Theme.hairline)
                    row("Age", "years", $age, .numberPad)
                }
                .padding(.horizontal, 16)
                .background(.white, in: RoundedRectangle(cornerRadius: 22, style: .continuous))

                Picker("Sex", selection: $sex) {
                    Text("Male").tag("male")
                    Text("Female").tag("female")
                }
                .pickerStyle(.segmented)

                Spacer()
                Button {
                    guard let input else { return }
                    saving = true
                    Task {
                        result = await store.saveProfile(input)
                        saving = false
                    }
                } label: {
                    if saving { ProgressView().tint(.white) } else { Text("Continue") }
                }
                .buttonStyle(BigButtonStyle())
                .disabled(input == nil || saving)
                .opacity(input == nil ? 0.4 : 1)
            }
        }
        .padding(.horizontal, 20).padding(.bottom, 20)
        .screen()
        .interactiveDismissDisabled(store.profile?.heightCm == nil && result == nil)
        .onAppear {
            guard let p = store.profile else { return }
            height = p.heightCm.map(fmt) ?? ""
            weight = p.weightKg.map(fmt) ?? ""
            age = p.age.map(String.init) ?? ""
            sex = p.sex ?? "male"
        }
    }

    private func row(_ label: String, _ unit: String, _ text: Binding<String>, _ keyboard: UIKeyboardType) -> some View {
        HStack {
            Text(label).font(Theme.text(15, .medium))
            Spacer()
            TextField("0", text: text)
                .keyboardType(keyboard)
                .multilineTextAlignment(.trailing)
                .font(Theme.mono(17))
                .frame(maxWidth: 120)
            Text(unit).font(Theme.text(13)).foregroundStyle(Theme.secondary).frame(width: 44, alignment: .leading)
        }
        .frame(minHeight: 52)
    }
}
