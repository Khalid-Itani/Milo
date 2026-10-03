import SwiftUI

struct EatView: View {
    @Environment(AppStore.self) private var store
    @State private var text = ""
    @State private var logging = false
    private let meals = [("breakfast", "Breakfast"), ("lunch", "Lunch"), ("snack", "Snacks"), ("dinner", "Dinner")]

    var body: some View {
        // List (not ScrollView) so meal rows get native swipe-to-delete.
        List {
            Group {
                header
                if let t = store.today { summary(t) }
                describeField
            }
            .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
            .listRowBackground(Color.clear)
            .listRowSeparator(.hidden)

            ForEach(meals, id: \.0) { key, title in
                mealSection(key: key, title: title, items: store.food?.meals[key] ?? [])
            }
        }
        .listStyle(.insetGrouped)
        .listSectionSpacing(10)
        .scrollContentBackground(.hidden)
        .scrollDismissesKeyboard(.interactively)
        .screen()
        .refreshable { await refresh() }
        .task { await refresh() }
    }

    private func refresh() async {
        async let a: () = store.refreshFood()
        async let b: () = store.refreshToday()
        _ = await (a, b)
    }

    private var header: some View {
        HStack {
            ScreenTitle(title: "Eat")
            Spacer()
            // ponytail: day paging is visual only; the MVP shows today.
            HStack(spacing: 2) {
                Image(systemName: "chevron.left").frame(width: 40, height: 40)
                Text("Today").font(Theme.text(14, .semibold)).padding(.horizontal, 4)
                Image(systemName: "chevron.right").foregroundStyle(Theme.fat).frame(width: 40, height: 40)
            }
            .font(.system(size: 14, weight: .semibold))
            .padding(2)
            .background(.white, in: Capsule())
        }
        .padding(.horizontal, 4)
    }

    private func summary(_ t: Today) -> some View {
        VStack(spacing: 14) {
            HStack(alignment: .bottom) {
                stat(fmt(t.kcal.target), "Goal")
                op("−")
                stat(fmt(t.kcal.eaten), "Food")
                op("=")
                stat(fmt(abs(t.kcal.left)), t.kcal.left < 0 ? "Over" : "Left", color: t.kcal.left < 0 ? Theme.train : Theme.fuel)
            }
            HStack(spacing: 12) {
                macro("Protein", t.macros.protein, Theme.fuel)
                macro("Carbs", t.macros.carbs, Theme.carbs)
                macro("Fat", t.macros.fat, Theme.fat)
            }
        }
        .card(22)
    }

    private func stat(_ value: String, _ label: String, color: Color = Theme.ink) -> some View {
        VStack(spacing: 0) {
            Text(value).font(Theme.mono(19)).foregroundStyle(color)
            Text(label).font(Theme.text(11.5)).foregroundStyle(Theme.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private func op(_ s: String) -> some View {
        Text(s).font(Theme.mono(17, .regular)).foregroundStyle(Color(hex: 0x8A8F98)).frame(width: 16).padding(.bottom, 16)
    }

    private func macro(_ name: String, _ m: Today.Macro, _ color: Color) -> some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(name).font(Theme.text(12, .medium))
                Spacer()
                Text(fmt(m.eaten)).font(Theme.mono(12, .regular)).foregroundStyle(Theme.secondary)
            }
            Bar(progress: m.target > 0 ? m.eaten / m.target : 0, color: color, height: 5)
            Text("of \(fmt(m.target)) g").font(Theme.text(11)).foregroundStyle(Theme.secondary)
        }
        .frame(maxWidth: .infinity)
    }

    private var describeField: some View {
        HStack(spacing: 4) {
            TextField("Describe what you ate…", text: $text)
                .font(Theme.text(15)).padding(.horizontal, 10).frame(height: 40)
                .submitLabel(.done)
                .onSubmit(logText)
                .disabled(logging)
            if logging {
                ProgressView().frame(width: 40, height: 40)
            } else {
                // ponytail: photo and barcode logging are out of MVP scope.
                Image(systemName: "camera").frame(width: 40, height: 40).background(Theme.trainTrack, in: Circle())
                    .accessibilityLabel("Snap a photo")
                Image(systemName: "barcode.viewfinder").frame(width: 40, height: 40).background(Theme.trainTrack, in: Circle())
                    .accessibilityLabel("Scan barcode")
            }
        }
        .font(.system(size: 15))
        .foregroundStyle(Theme.ink)
        .padding(6)
        .background(.white, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        .overlay(RoundedRectangle(cornerRadius: 24, style: .continuous).stroke(Theme.border))
    }

    private func logText() {
        let t = text.trimmingCharacters(in: .whitespaces)
        guard !t.isEmpty else { return }
        text = ""
        logging = true
        Task {
            await store.send("Log for \(Self.mealNow): \(t)") // send() refreshes food + today
            logging = false
        }
    }

    static var mealNow: String {
        switch Calendar.current.component(.hour, from: Date()) {
        case ..<11: "breakfast"
        case ..<16: "lunch"
        case ..<18: "snack"
        default: "dinner"
        }
    }

    @ViewBuilder
    private func mealSection(key: String, title: String, items: [FoodLog]) -> some View {
        Section {
            HStack(alignment: .firstTextBaseline) {
                Text(title).font(Theme.text(15, .semibold))
                Spacer()
                if items.isEmpty {
                    Text("Not logged").font(Theme.text(12.5)).foregroundStyle(Theme.secondary)
                } else {
                    Text(fmt(items.map(\.kcal).reduce(0, +))).font(Theme.mono(14))
                }
            }
            .listRowSeparator(.hidden)

            ForEach(items) { item in
                FoodRow(item: item)
                    .listRowSeparator(.hidden)
                    .swipeActions {
                        Button("Delete", role: .destructive) { Task { await store.deleteFood(item.id) } }
                    }
            }

            if key == "dinner" && items.isEmpty {
                DinnerSuggestion().listRowSeparator(.hidden)
            }
        }
        .listRowBackground(Color.white)
    }
}

private struct FoodRow: View {
    var item: FoodLog
    var body: some View {
        HStack(spacing: 10) {
            VStack(alignment: .leading, spacing: 1) {
                Text(item.name).font(Theme.text(14, .medium))
                (Text("\(item.quantity) · \(fmt(item.proteinG)) P · \(fmt(item.carbsG)) C · \(fmt(item.fatG)) F")
                    + (item.source == "coach" ? Text(" · ") + Text("via Milo").foregroundColor(Theme.fuel).fontWeight(.medium) : Text("")))
                    .font(Theme.text(12)).foregroundColor(Theme.secondary)
            }
            Spacer()
            Text(fmt(item.kcal)).font(Theme.mono(13.5, .regular)).foregroundStyle(Theme.tertiary)
        }
        .frame(minHeight: 44)
    }
}

/// Shown when dinner is empty. Hardcoded from the mockup for speed (SPEC §4.3 allows it).
private struct DinnerSuggestion: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Label("Milo suggests", systemImage: "sparkles").font(Theme.text(12, .semibold)).foregroundStyle(Theme.fuelDeep)
            VStack(alignment: .leading, spacing: 1) {
                Text("Salmon, rice & broccoli").font(Theme.text(15, .semibold))
                Text("780 kcal · 48 g protein · fits what’s left today").font(Theme.text(12.5)).foregroundStyle(Theme.tertiary)
            }
            HStack(spacing: 8) {
                Button("Log it") {
                    Task {
                        await store.logFood(NewFood(date: Dates.todayString, meal: "dinner", name: "Salmon, rice & broccoli",
                                                    quantity: "1 plate", kcal: 780, proteinG: 48, carbsG: 80, fatG: 26, source: "coach"))
                    }
                }
                .buttonStyle(BigButtonStyle(bg: Theme.fuel, radius: 12))
                Button("Other ideas") { store.openCoach(prefill: "Suggest a different dinner that fits my remaining macros") }
                    .buttonStyle(BigButtonStyle(bg: .white, fg: Theme.ink, radius: 12))
            }
        }
        .padding(.horizontal, 14).padding(.vertical, 12)
        .background(Theme.fuelTint, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
        .padding(.bottom, 4)
    }
}
