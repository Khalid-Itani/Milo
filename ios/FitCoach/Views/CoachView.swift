import SwiftUI

struct CoachView: View {
    @Environment(AppStore.self) private var store
    @FocusState private var focused: Bool
    private let suggestions = ["Plan tonight’s dinner", "Swap an exercise", "How was my week?"]

    var body: some View {
        @Bindable var store = store
        VStack(spacing: 0) {
            HStack {
                ScreenTitle(title: "Coach")
                Spacer()
                // ponytail: past chats / new chat are visual only in the MVP.
                Button {} label: { Image(systemName: "clock.arrow.circlepath").frame(width: 44, height: 44) }
                    .accessibilityLabel("Past chats")
                Button {} label: { Image(systemName: "square.and.pencil").frame(width: 44, height: 44) }
                    .accessibilityLabel("New chat")
            }
            .font(.system(size: 18))
            .foregroundStyle(Theme.ink)
            .padding(.leading, 20).padding(.trailing, 12).padding(.top, 8)

            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 14) {
                        ForEach(store.chat) { MessageView(message: $0) }
                        if store.isSending {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 22, weight: .bold)).foregroundStyle(Theme.secondary)
                                .symbolEffect(.variableColor.iterative)
                                .accessibilityLabel("Coach is typing")
                        }
                        Color.clear.frame(height: 1).id("bottom")
                    }
                    .padding(.horizontal, 16).padding(.vertical, 12)
                }
                .scrollDismissesKeyboard(.interactively)
                .onChange(of: store.chat.count) { withAnimation { proxy.scrollTo("bottom") } }
                .onChange(of: store.isSending) { withAnimation { proxy.scrollTo("bottom") } }
                .onAppear { proxy.scrollTo("bottom") }
            }

            inputArea(draft: $store.coachDraft)
        }
        .screen()
        .task { await store.loadChat() }
        .onAppear { if !store.coachDraft.isEmpty { focused = true } }
        .onChange(of: store.coachDraft) { _, new in if !new.isEmpty && !focused { focused = true } }
    }

    private func inputArea(draft: Binding<String>) -> some View {
        VStack(spacing: 10) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(suggestions, id: \.self) { s in
                        Button { Task { await store.send(s) } } label: {
                            Text(s).font(Theme.text(13, .medium)).foregroundStyle(Theme.ink)
                                .padding(.horizontal, 14).frame(height: 36)
                                .background(.white, in: Capsule())
                                .overlay(Capsule().stroke(Theme.border))
                        }
                        .disabled(store.isSending)
                    }
                }
                .padding(.horizontal, 12)
            }
            HStack(spacing: 4) {
                Button {} label: {
                    Image(systemName: "plus").frame(width: 40, height: 40).background(Theme.trainTrack, in: Circle())
                }
                .accessibilityLabel("Add photo or barcode")
                TextField("Ask, log a meal, plan a workout", text: draft, axis: .vertical)
                    .font(Theme.text(15)).lineLimit(1...4)
                    .padding(.horizontal, 6)
                    .focused($focused)
                    .submitLabel(.send)
                    .onSubmit(submit)
                Button {} label: { Image(systemName: "mic").foregroundStyle(Theme.secondary).frame(width: 40, height: 40) }
                    .accessibilityLabel("Dictate")
                Button(action: submit) {
                    Image(systemName: "arrow.up").font(.system(size: 16, weight: .semibold)).foregroundStyle(.white)
                        .frame(width: 40, height: 40).background(Theme.ink, in: Circle())
                }
                .accessibilityLabel("Send")
                .disabled(store.isSending || draft.wrappedValue.trimmingCharacters(in: .whitespaces).isEmpty)
            }
            .foregroundStyle(Theme.ink)
            .padding(6)
            .background(.white, in: RoundedRectangle(cornerRadius: 26, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 26, style: .continuous).stroke(Theme.border))
            .shadow(color: Theme.ink.opacity(0.06), radius: 10, y: 6)
            .padding(.horizontal, 12)
        }
        .padding(.top, 10).padding(.bottom, 12)
        .background(Theme.bg)
    }

    private func submit() {
        let text = store.coachDraft
        store.coachDraft = ""
        Task { await store.send(text) }
    }
}

private struct MessageView: View {
    var message: ChatMessage

    var body: some View {
        if message.role == "user" {
            Text(message.content)
                .font(Theme.text(15)).foregroundStyle(.white).lineSpacing(3)
                .padding(.horizontal, 14).padding(.vertical, 11)
                .background(Theme.ink, in: UnevenRoundedRectangle(topLeadingRadius: 20, bottomLeadingRadius: 20, bottomTrailingRadius: 6, topTrailingRadius: 20, style: .continuous))
                .frame(maxWidth: 290, alignment: .trailing)
                .frame(maxWidth: .infinity, alignment: .trailing)
        } else {
            VStack(alignment: .leading, spacing: 10) {
                if !message.content.isEmpty {
                    Text(message.content).font(Theme.text(15)).lineSpacing(4).foregroundStyle(Theme.ink)
                }
                ForEach(Array((message.cards ?? []).enumerated()), id: \.offset) { _, card in
                    CardView(card: card)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

// MARK: Cards

private struct CardView: View {
    var card: Card
    var body: some View {
        switch card {
        case .workoutPlan(let p): PlanCardView(plan: p)
        case .foodLogged(let f): FoodCardView(food: f)
        case .dietPlan(let d): DietCardView(plan: d)
        case .goalSet(let g):
            IconCard(icon: "target", tint: Theme.ink, bg: Theme.trainTrack, kicker: "Goal set", title: g.title,
                     trailing: "\(fmt(g.targetValue)) \(g.unit)",
                     detail: g.deadline.map { "by \(Dates.format($0, "MMM d, yyyy"))" })
        case .setLogged(let s):
            IconCard(icon: "checkmark", tint: Theme.ink, bg: Theme.train, kicker: "Set logged", title: s.exercise,
                     trailing: "\(fmt(s.kg)) × \(s.reps)", detail: nil)
        case .unknown: EmptyView()
        }
    }
}

private struct CardShell<Content: View>: View {
    @ViewBuilder var content: Content
    var body: some View {
        content
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(.white, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous).stroke(Color(hex: 0xE6E4DF)))
    }
}

private struct PlanCardView: View {
    @Environment(AppStore.self) private var store
    var plan: PlanCard

    var body: some View {
        CardShell {
            VStack(spacing: 0) {
                HStack {
                    Text(plan.planName).font(Theme.text(15, .semibold))
                    Spacer()
                    if let w = plan.weeks { Pill(text: "\(w) weeks") }
                }
                .padding(.horizontal, 14).padding(.top, 14).padding(.bottom, 10)
                ForEach(Array(plan.workouts.enumerated()), id: \.offset) { _, d in
                    Divider().overlay(Theme.hairline)
                    HStack(alignment: .top, spacing: 10) {
                        Text(d.dayLabel).font(Theme.mono(12)).foregroundStyle(Theme.secondary).frame(width: 40, alignment: .leading)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(d.name).font(Theme.text(13.5, .semibold))
                            Text(d.summary).font(Theme.text(12.5)).foregroundStyle(Theme.secondary)
                        }
                        Spacer(minLength: 0)
                    }
                    .padding(.horizontal, 14).padding(.vertical, 9)
                }
                Divider().overlay(Theme.hairline)
                HStack(spacing: 8) {
                    // The plan is already saved by the tool call; this just jumps to Train.
                    Button("Save to Train") { store.trainPath = []; store.selectedTab = .train }
                        .buttonStyle(BigButtonStyle())
                    Button("Adjust") { store.coachDraft = "Adjust the plan: " }
                        .buttonStyle(BigButtonStyle(bg: .white, fg: Theme.ink, border: Theme.border))
                }
                .padding(.horizontal, 14).padding(.top, 12).padding(.bottom, 14)
            }
        }
    }
}

private struct FoodCardView: View {
    @Environment(AppStore.self) private var store
    var food: FoodCard

    var body: some View {
        let undone = store.undoneFoodIds.contains(food.id)
        CardShell {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 10) {
                    Image(systemName: undone ? "arrow.uturn.backward" : "checkmark")
                        .font(.system(size: 14, weight: .bold)).foregroundStyle(Theme.fuel)
                        .frame(width: 32, height: 32).background(Theme.fuelTint2, in: RoundedRectangle(cornerRadius: 10))
                    VStack(alignment: .leading, spacing: 0) {
                        Text(undone ? "Removed" : "Logged to \(food.meal.capitalized)").font(Theme.text(12, .semibold)).foregroundStyle(Theme.fuel)
                        Text(food.name).font(Theme.text(14, .semibold)).strikethrough(undone)
                    }
                    Spacer()
                    Text(fmt(food.kcal)).font(Theme.mono(14))
                }
                HStack(spacing: 6) {
                    Chip(text: "\(fmt(food.proteinG)) P")
                    Chip(text: "\(fmt(food.carbsG)) C")
                    Chip(text: "\(fmt(food.fatG)) F")
                    Spacer()
                    if !undone {
                        Button("Undo") { Task { await store.deleteFood(food.id) } }
                            .font(Theme.text(13, .semibold)).foregroundStyle(Theme.secondary)
                            .frame(minHeight: 44)
                    }
                }
            }
            .padding(.horizontal, 14).padding(.vertical, 12)
        }
    }
}

private struct DietCardView: View {
    var plan: DietPlan
    var body: some View {
        CardShell {
            VStack(alignment: .leading, spacing: 0) {
                HStack {
                    Text(plan.name).font(Theme.text(15, .semibold))
                    Spacer()
                    Pill(text: "\(fmt(plan.kcal)) kcal", fg: Theme.fuelDeep, bg: Theme.fuelTint2)
                }
                .padding(.horizontal, 14).padding(.top, 14).padding(.bottom, 10)
                ForEach(Array(plan.meals.enumerated()), id: \.offset) { _, m in
                    Divider().overlay(Theme.hairline)
                    HStack(alignment: .top, spacing: 10) {
                        Text(m.meal.prefix(5).uppercased()).font(Theme.mono(11)).foregroundStyle(Theme.secondary).frame(width: 46, alignment: .leading)
                        VStack(alignment: .leading, spacing: 1) {
                            Text(m.name).font(Theme.text(13.5, .semibold))
                            Text("\(fmt(m.proteinG)) P · \(fmt(m.carbsG)) C · \(fmt(m.fatG)) F")
                                .font(Theme.mono(12, .regular)).foregroundStyle(Theme.secondary)
                        }
                        Spacer()
                        Text(fmt(m.kcal)).font(Theme.mono(13))
                    }
                    .padding(.horizontal, 14).padding(.vertical, 9)
                }
            }
        }
    }
}

private struct IconCard: View {
    var icon: String
    var tint: Color
    var bg: Color
    var kicker: String
    var title: String
    var trailing: String
    var detail: String?

    var body: some View {
        CardShell {
            HStack(spacing: 10) {
                Image(systemName: icon).font(.system(size: 14, weight: .bold)).foregroundStyle(tint)
                    .frame(width: 32, height: 32).background(bg, in: RoundedRectangle(cornerRadius: 10))
                VStack(alignment: .leading, spacing: 0) {
                    Text(kicker).font(Theme.text(12, .semibold)).foregroundStyle(Theme.secondary)
                    Text(title).font(Theme.text(14, .semibold))
                    if let detail { Text(detail).font(Theme.text(12.5)).foregroundStyle(Theme.secondary) }
                }
                Spacer()
                Text(trailing).font(Theme.mono(14))
            }
            .padding(.horizontal, 14).padding(.vertical, 12)
        }
    }
}
