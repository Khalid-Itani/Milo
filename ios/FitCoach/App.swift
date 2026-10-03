import SwiftUI

@main
struct FitCoachApp: App {
    @State private var store = AppStore()
    var body: some Scene {
        WindowGroup {
            RootView().environment(store)
        }
    }
}

enum Tab: Hashable { case today, coach, train, eat, goals }

struct RootView: View {
    @Environment(AppStore.self) private var store

    var body: some View {
        @Bindable var store = store
        TabView(selection: $store.selectedTab) {
            TodayView().tabItem { Label("Today", systemImage: "square.grid.2x2") }.tag(Tab.today)
            CoachView().tabItem { Label("Coach", systemImage: "bubble.left") }.tag(Tab.coach)
            TrainView().tabItem { Label("Train", systemImage: "dumbbell") }.tag(Tab.train)
            EatView().tabItem { Label("Eat", systemImage: "fork.knife") }.tag(Tab.eat)
            GoalsView().tabItem { Label("Goals", systemImage: "target") }.tag(Tab.goals)
        }
        .tint(Theme.ink)
        .sheet(isPresented: $store.showOnboarding) { OnboardingView() }
        .task { await store.loadProfile() }
        .alert("Something went wrong", isPresented: Binding(get: { store.error != nil }, set: { if !$0 { store.error = nil } })) {
            Button("OK") { store.error = nil }
        } message: { Text(store.error ?? "") }
    }
}

/// One store for every tab. Each tab calls its refresh on appear; mutations refresh what they touch.
@Observable @MainActor
final class AppStore {
    var selectedTab: Tab = .today
    var coachDraft = ""          // prefilled by "Adjust", "New goal", etc.
    var trainPath: [Int] = []    // workout ids pushed in the Train tab
    var showOnboarding = false
    var error: String?

    var profile: User?
    var today: Today?
    var workouts: [Workout] = []
    var food: FoodDay?
    var goals: [Goal] = []
    var scans: [Scan] = []
    var chat: [ChatMessage] = []
    var isSending = false
    var undoneFoodIds: Set<Int> = []

    private let api = APIClient.shared

    private func run(_ work: () async throws -> Void) async {
        do { try await work() } catch is CancellationError {} catch let e as URLError where e.code == .cancelled {} catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: Loads

    func loadProfile() async {
        await run {
            let user: User = try await api.get("/profile")
            profile = user
            showOnboarding = user.heightCm == nil
        }
    }
    func refreshToday() async { await run { today = try await api.get("/today") } }
    func refreshWorkouts() async { await run { workouts = try await api.get("/workouts") } }
    func refreshFood() async { await run { food = try await api.get("/food?date=\(Dates.todayString)") } }
    func refreshGoals() async { await run { goals = try await api.get("/goals") } }
    func refreshScans() async { await run { scans = try await api.get("/scans") } }
    func loadChat() async {
        guard !isSending else { return } // don't clobber the optimistic message mid-request
        await run { chat = try await api.get("/chat/history") }
    }

    // MARK: Profile

    func saveProfile(_ input: ProfileInput) async -> User? {
        var saved: User?
        await run {
            saved = try await api.post("/profile", input)
            profile = saved
        }
        await refreshToday()
        return saved
    }

    // MARK: Body scan (Visualize AI)

    func visualizeSessionToken() async throws -> String {
        let session: VisualizeSession = try await api.post("/visualize/session")
        return session.sessionToken
    }

    func allowScanStorage() async {
        await run { profile = try await api.post("/profile", ConsentInput(scanStorageConsent: true)) }
    }

    func saveBodyScan(metrics: [ScanMetric]) async {
        await run { let _: Scan = try await api.post("/scans", ScanInput(metrics: metrics)) }
        await refreshToday()
    }

    // MARK: Coach

    func send(_ text: String) async {
        let message = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !message.isEmpty, !isSending else { return }
        chat.append(ChatMessage(id: -(chat.count + 1), role: "user", content: message, cards: []))
        isSending = true
        defer { isSending = false }
        await run {
            let reply: ChatReply = try await api.post("/chat", ChatInput(message: message))
            chat.append(ChatMessage(id: -(chat.count + 1), role: "assistant", content: reply.reply, cards: reply.cards))
        }
        // Tools may have touched any tab's data.
        async let a: () = refreshToday()
        async let b: () = refreshFood()
        async let c: () = refreshWorkouts()
        async let d: () = refreshGoals()
        _ = await (a, b, c, d)
    }

    func openCoach(prefill: String = "") {
        coachDraft = prefill
        selectedTab = .coach
    }

    // MARK: Train

    func startWorkout(_ id: Int) async {
        await run { let _: Workout = try await api.post("/workouts/\(id)/start") }
        await refreshWorkouts()
    }

    func finishWorkout(_ id: Int) async {
        await run { let _: Workout = try await api.post("/workouts/\(id)/finish") }
        await refreshWorkouts()
        await refreshToday()
    }

    func addSet(exerciseId: Int, kg: Double, reps: Int) async {
        await run { let _: WorkoutSet = try await api.post("/exercises/\(exerciseId)/sets", NewSet(kg: kg, reps: reps)) }
        await refreshWorkouts()
    }

    func updateSet(_ id: Int, _ patch: SetPatch) async {
        await run { let _: WorkoutSet = try await api.patch("/sets/\(id)", patch) }
        await refreshWorkouts()
    }

    // MARK: Eat

    func logFood(_ food: NewFood) async {
        await run { let _: FoodLog = try await api.post("/food", food) }
        await refreshFood()
        await refreshToday()
    }

    func deleteFood(_ id: Int) async {
        await run {
            try await api.delete("/food/\(id)")
            undoneFoodIds.insert(id)
        }
        await refreshFood()
        await refreshToday()
    }
}
