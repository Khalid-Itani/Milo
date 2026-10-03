import SwiftUI

struct TrainView: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        @Bindable var store = store
        NavigationStack(path: $store.trainPath) {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    ScreenTitle(title: "Train").padding(.horizontal, 4)
                    group("Active", store.workouts.filter { $0.status == "active" })
                    group("Up next", store.workouts.filter { $0.status == "planned" })
                    group("Done", store.workouts.filter { $0.status == "done" })
                    if store.workouts.isEmpty {
                        DashedRow(text: "Ask Milo to build a training plan") { store.openCoach(prefill: "Build me a training plan: ") }
                    }
                }
                .padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 24)
            }
            .screen()
            .toolbar(.hidden, for: .navigationBar)
            .refreshable { await store.refreshWorkouts() }
            .task { await store.refreshWorkouts() }
            .navigationDestination(for: Int.self) { WorkoutDetailView(id: $0) }
        }
    }

    @ViewBuilder
    private func group(_ title: String, _ items: [Workout]) -> some View {
        if !items.isEmpty {
            Text(title).font(Theme.text(13, .semibold)).foregroundStyle(Theme.secondary).padding(.horizontal, 4).padding(.top, 6)
            VStack(spacing: 0) {
                ForEach(Array(items.enumerated()), id: \.element.id) { i, w in
                    if i > 0 { Divider().overlay(Theme.hairline) }
                    NavigationLink(value: w.id) { WorkoutRow(workout: w) }.buttonStyle(.plain)
                }
            }
            .background(.white, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
    }
}

private struct WorkoutRow: View {
    var workout: Workout
    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Text(workout.dayLabel).font(Theme.mono(12)).foregroundStyle(Theme.secondary).frame(width: 40, alignment: .leading).padding(.top, 2)
            VStack(alignment: .leading, spacing: 2) {
                Text(workout.name).font(Theme.text(15, .semibold))
                Text(summary).font(Theme.text(12.5)).foregroundStyle(Theme.secondary).lineLimit(1)
            }
            Spacer()
            if workout.status == "done" {
                Image(systemName: "checkmark").font(.system(size: 11, weight: .bold)).foregroundStyle(Theme.ink)
                    .frame(width: 22, height: 22).background(Theme.train, in: Circle())
            } else {
                Image(systemName: "chevron.right").font(.system(size: 13, weight: .semibold)).foregroundStyle(Theme.fat)
            }
        }
        .padding(.horizontal, 16).padding(.vertical, 12)
        .contentShape(Rectangle())
    }

    private var summary: String {
        let names = workout.exercises.sorted { $0.position < $1.position }.map(\.name)
        return names.isEmpty ? workout.status.capitalized : names.joined(separator: " · ")
    }
}

// MARK: Detail

struct WorkoutDetailView: View {
    @Environment(AppStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    var id: Int

    private var workout: Workout? { store.workouts.first { $0.id == id } }

    var body: some View {
        ScrollView {
            if let w = workout {
                VStack(spacing: 12) {
                    header(w)
                    stats(w)
                    ForEach(w.exercises.sorted { $0.position < $1.position }) { ExerciseCard(exercise: $0, editable: w.status != "planned") } // finished sessions stay editable
                }
                .padding(.horizontal, 16).padding(.bottom, 24)
            } else {
                ProgressView().padding(.top, 80)
            }
        }
        .scrollDismissesKeyboard(.interactively)
        .toolbar {
            ToolbarItemGroup(placement: .keyboard) {
                Spacer()
                Button("Done") { UIApplication.shared.sendAction(#selector(UIResponder.resignFirstResponder), to: nil, from: nil, for: nil) }
            }
        }
        .screen()
        .navigationBarTitleDisplayMode(.inline)
        .task { if workout == nil { await store.refreshWorkouts() } }
    }

    private func header(_ w: Workout) -> some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 2) {
                Text(subtitle(w)).font(Theme.text(13, .medium)).foregroundStyle(Theme.secondary)
                ScreenTitle(title: w.name, size: 26)
            }
            Spacer()
            switch w.status {
            case "planned": Button("Start") { Task { await store.startWorkout(w.id) } }.buttonStyle(PillButtonStyle())
            case "active":
                Button("Finish") {
                    Task {
                        await store.finishWorkout(w.id)
                        dismiss()
                    }
                }
                .buttonStyle(PillButtonStyle())
            default: EmptyView()
            }
        }
        .padding(.horizontal, 4)
    }

    private func subtitle(_ w: Workout) -> String {
        guard let start = Dates.parse(w.startedAt) else { return "\(w.dayLabel) · Not started" }
        let time = start.formatted(date: .omitted, time: .shortened)
        return w.status == "done" ? "Done · started \(time)" : "Started \(time)"
    }

    private func stats(_ w: Workout) -> some View {
        let done = w.exercises.flatMap(\.sets).filter(\.done)
        let volume = done.reduce(0) { $0 + $1.kg * Double($1.reps) }
        return HStack(spacing: 0) {
            TimelineView(.periodic(from: .now, by: 1)) { ctx in
                stat("Duration", duration(w, now: ctx.date))
            }
            Divider().overlay(Theme.hairline)
            stat("Volume", "\(fmt(volume)) kg")
            Divider().overlay(Theme.hairline)
            stat("Sets", "\(done.count)")
        }
        .padding(.vertical, 12).padding(.horizontal, 4)
        .background(.white, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
    }

    private func stat(_ label: String, _ value: String) -> some View {
        VStack(spacing: 2) {
            Text(label).font(Theme.text(11.5, .medium)).foregroundStyle(Theme.secondary)
            Text(value).font(Theme.mono(18))
        }
        .frame(maxWidth: .infinity)
    }

    private func duration(_ w: Workout, now: Date) -> String {
        guard let start = Dates.parse(w.startedAt) else { return "0:00" }
        let end = Dates.parse(w.finishedAt) ?? now
        let s = max(0, Int(end.timeIntervalSince(start)))
        return s >= 3600 ? String(format: "%d:%02d:%02d", s / 3600, s / 60 % 60, s % 60) : String(format: "%d:%02d", s / 60, s % 60)
    }
}

/// SET / PREVIOUS / KG / REPS / check columns, as in design/Train.html.
private struct SetGrid<A: View, B: View, C: View, D: View, E: View>: View {
    @ViewBuilder var set: A
    @ViewBuilder var previous: B
    @ViewBuilder var kg: C
    @ViewBuilder var reps: D
    @ViewBuilder var check: E
    var body: some View {
        HStack(spacing: 6) {
            set.frame(width: 36)
            previous.frame(maxWidth: .infinity, alignment: .leading)
            kg.frame(width: 64)
            reps.frame(width: 54)
            check.frame(width: 44)
        }
    }
}

private struct ExerciseCard: View {
    @Environment(AppStore.self) private var store
    var exercise: Exercise
    var editable: Bool

    private var sets: [WorkoutSet] { exercise.sets.sorted { $0.setIndex < $1.setIndex } }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(exercise.name).font(Theme.text(16, .semibold)).padding(.horizontal, 4)
            SetGrid { Text("SET") } previous: { Text("PREVIOUS") } kg: { Text("KG") } reps: { Text("REPS") } check: { Color.clear.frame(height: 1) }
                .font(Theme.text(11, .semibold)).tracking(0.4).foregroundStyle(Theme.secondary)
                .padding(.horizontal, 4)
            VStack(spacing: 2) {
                ForEach(Array(sets.enumerated()), id: \.element.id) { i, s in
                    SetRow(set: s, label: s.isWarmup ? "W" : "\(sets[..<i].filter { !$0.isWarmup }.count + 1)",
                           previous: previous, editable: editable)
                }
            }
            if editable {
                Button {
                    let last = sets.last
                    Task { await store.addSet(exerciseId: exercise.id, kg: last?.kg ?? exercise.targetKg ?? 0, reps: last?.reps ?? exercise.targetReps) }
                } label: {
                    Label("Add set", systemImage: "plus")
                }
                .buttonStyle(BigButtonStyle(bg: Color(hex: 0xF5F4F1), fg: Theme.ink, radius: 12))
            }
        }
        .padding(.horizontal, 12).padding(.top, 14).padding(.bottom, 10)
        .background(.white, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    // ponytail: no per-exercise history endpoint, so PREVIOUS shows the plan's target.
    private var previous: String {
        guard let kg = exercise.targetKg else { return "— × \(exercise.targetReps)" }
        return "\(fmt(kg)) × \(exercise.targetReps)"
    }
}

private struct SetRow: View {
    @Environment(AppStore.self) private var store
    var set: WorkoutSet
    var label: String
    var previous: String
    var editable: Bool
    @State private var kg = ""
    @State private var reps = ""
    @FocusState private var focused: Bool

    var body: some View {
        SetGrid {
            Text(label).font(Theme.mono(14)).foregroundStyle(set.isWarmup ? Color(hex: 0xB4430F) : Theme.ink)
        } previous: {
            Text(previous).font(Theme.mono(13, .regular)).foregroundStyle(Theme.secondary).lineLimit(1)
        } kg: {
            field($kg, placeholder: fmt(set.kg), keyboard: .decimalPad)
        } reps: {
            field($reps, placeholder: "\(set.reps)", keyboard: .numberPad)
        } check: {
            Button(action: toggle) {
                Image(systemName: "checkmark").font(.system(size: 13, weight: .bold))
                    .foregroundStyle(set.done ? Theme.ink : Theme.fat)
                    .frame(width: 32, height: 32)
                    .background(set.done ? Theme.train : .white, in: RoundedRectangle(cornerRadius: 9))
                    .overlay { if !set.done { RoundedRectangle(cornerRadius: 9).stroke(Color(hex: 0xCFCDC7), lineWidth: 1.5) } }
                    .frame(width: 44, height: 44)
            }
            .disabled(!editable)
            .accessibilityLabel(set.done ? "Set complete" : "Mark set complete")
        }
        .frame(height: 44)
        .padding(.horizontal, 4)
        .background(set.done ? Theme.trainTint : .clear, in: RoundedRectangle(cornerRadius: 10))
        .onAppear { kg = fmt(set.kg); reps = "\(set.reps)" }
        .onChange(of: set.kg) { kg = fmt(set.kg) }
        .onChange(of: set.reps) { reps = "\(set.reps)" }
        .onChange(of: focused) { if !focused { save() } } // number pads have no return key
    }

    private func field(_ text: Binding<String>, placeholder: String, keyboard: UIKeyboardType) -> some View {
        TextField(placeholder, text: text)
            .keyboardType(keyboard)
            .multilineTextAlignment(.center)
            .font(Theme.mono(14))
            .frame(height: 34)
            .background(set.done ? .clear : Theme.field, in: RoundedRectangle(cornerRadius: 9))
            .disabled(!editable)
            .focused($focused)
            .onSubmit(save)
    }

    private func parsed() -> (Double?, Int?) {
        (Double(kg.replacingOccurrences(of: ",", with: ".")), Int(reps))
    }

    private func save() {
        let (k, r) = parsed()
        guard k != set.kg || r != set.reps else { return }
        Task { await store.updateSet(set.id, SetPatch(kg: k, reps: r)) }
    }

    private func toggle() {
        let (k, r) = parsed()
        Task { await store.updateSet(set.id, SetPatch(kg: k, reps: r, done: !set.done)) }
    }
}
