import SwiftUI

struct GoalsView: View {
    @Environment(AppStore.self) private var store
    @State private var showCompleted = false

    var body: some View {
        let active = store.goals.filter { $0.status != "completed" }
        let completed = store.goals.filter { $0.status == "completed" }
        let shown = showCompleted ? completed : active
        let large = shown.filter { $0.kind == "strength" || $0.kind == "body" }
        let compact = shown.filter { $0.kind != "strength" && $0.kind != "body" }

        ScrollView {
            VStack(spacing: 12) {
                HStack {
                    ScreenTitle(title: "Goals")
                    Spacer()
                    Button { store.openCoach(prefill: "Set a goal: ") } label: {
                        Label("New goal", systemImage: "plus")
                            .font(Theme.text(14, .semibold)).foregroundStyle(.white)
                            .padding(.leading, 10).padding(.trailing, 14).frame(height: 44)
                            .background(Theme.ink, in: Capsule())
                    }
                }
                .padding(.horizontal, 4)

                segmented(active: active.count, completed: completed.count)

                ForEach(large) { LargeGoalCard(goal: $0) }
                LazyVGrid(columns: [GridItem(.flexible(), spacing: 10), GridItem(.flexible())], spacing: 10) {
                    ForEach(compact) { CompactGoalCard(goal: $0) }
                }
                if shown.isEmpty {
                    Text(showCompleted ? "No completed goals yet." : "No active goals.")
                        .font(Theme.text(14)).foregroundStyle(Theme.secondary).padding(.vertical, 20)
                }
                DashedRow(text: "Tell Milo what you want to achieve") { store.openCoach(prefill: "Set a goal: ") }
            }
            .padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 24)
        }
        .screen()
        .refreshable { await store.refreshGoals() }
        .task { await store.refreshGoals() }
    }

    private func segmented(active: Int, completed: Int) -> some View {
        HStack(spacing: 0) {
            segment("Active · \(active)", selected: !showCompleted) { showCompleted = false }
            segment("Completed · \(completed)", selected: showCompleted) { showCompleted = true }
        }
        .padding(3)
        .background(Color(hex: 0xE9E8E4), in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func segment(_ title: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title).font(Theme.text(13.5, selected ? .semibold : .medium))
                .foregroundStyle(selected ? Theme.ink : Theme.tertiary)
                .frame(maxWidth: .infinity, minHeight: 38)
                .background(selected ? Color.white : .clear, in: RoundedRectangle(cornerRadius: 11, style: .continuous))
                .shadow(color: selected ? Theme.ink.opacity(0.08) : .clear, radius: 1.5, y: 1)
        }
        .buttonStyle(.plain)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

private struct LargeGoalCard: View {
    var goal: Goal
    private var isStrength: Bool { goal.kind == "strength" }
    private var accent: Color { isStrength ? Theme.train : Theme.fuel }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Pill(text: goal.kind.capitalized,
                     fg: isStrength ? Color(hex: 0xA33C0D) : Theme.fuelDeep,
                     bg: isStrength ? Theme.trainTint : Theme.fuelTint2)
                if let d = goal.deadline { Text("by \(Dates.format(d, "MMM d"))").font(Theme.text(12.5)).foregroundStyle(Theme.secondary) }
                Spacer()
                if goal.status == "completed" { Text("Completed").font(Theme.text(12.5, .semibold)) }
            }
            Text(goal.title).font(Theme.text(16, .semibold))
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(fmt(goal.currentValue)).font(Theme.mono(34)).tracking(-1.2)
                Text("/ \(fmt(goal.targetValue)) \(goal.unit)").font(Theme.mono(15, .regular)).foregroundStyle(Theme.secondary)
            }
            VStack(spacing: 6) {
                Bar(progress: goal.progress, color: accent, track: isStrength ? Theme.trainTrack : Theme.barTrack, height: 8)
                HStack {
                    Text("\(fmt(goal.startValue)) \(goal.unit) start")
                    Spacer()
                    Text("\(Int((goal.progress * 100).rounded()))%")
                }
                .font(Theme.mono(11.5, .regular)).foregroundStyle(Theme.secondary)
            }
        }
        .card(22)
    }
}

private struct CompactGoalCard: View {
    var goal: Goal
    private var isHabit: Bool { goal.kind == "habit" }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(goal.title).font(Theme.text(14, .semibold)).lineLimit(2, reservesSpace: true)
            if isHabit && goal.targetValue >= 1 && goal.targetValue <= 7 {
                // One block per session, e.g. 3 of 4 filled.
                HStack(spacing: 4) {
                    ForEach(0..<Int(goal.targetValue), id: \.self) { i in
                        if Double(i) < goal.currentValue {
                            RoundedRectangle(cornerRadius: 6).fill(Theme.train)
                        } else {
                            RoundedRectangle(cornerRadius: 6).strokeBorder(Theme.dashed, style: StrokeStyle(lineWidth: 1.5, dash: [4, 3]))
                        }
                    }
                }
                .frame(height: 26)
            } else {
                Bar(progress: goal.progress, color: isHabit ? Theme.train : Theme.fuel, height: 8)
                    .frame(height: 26)
            }
            Text("\(fmt(goal.currentValue)) of \(fmt(goal.targetValue)) \(goal.unit)")
                .font(Theme.text(12)).foregroundStyle(Theme.secondary)
        }
        .card(20, padding: 14)
    }
}
