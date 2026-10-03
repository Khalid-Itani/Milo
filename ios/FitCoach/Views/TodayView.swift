import SwiftUI

struct TodayView: View {
    @Environment(AppStore.self) private var store
    @State private var showProfile = false

    var body: some View {
        ScrollView {
            VStack(spacing: 12) {
                header
                if let t = store.today {
                    tipCard(t.coachTip)
                    fuelCard(t)
                    metrics(t)
                    weekCard(t)
                } else {
                    ProgressView().padding(.top, 80)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 8)
            .padding(.bottom, 24)
        }
        .screen()
        .refreshable { await store.refreshToday() }
        .task { await store.refreshToday() }
        .sheet(isPresented: $showProfile) { OnboardingView() }
    }

    private var header: some View {
        HStack(alignment: .bottom) {
            VStack(alignment: .leading, spacing: 2) {
                Text(Dates.format(store.today?.date ?? Dates.todayString, "MMMM d"))
                    .font(Theme.text(13, .medium)).foregroundStyle(Theme.secondary)
                ScreenTitle(title: "Today", size: 32)
            }
            Spacer()
            Button { showProfile = true } label: {
                Text(String(store.profile?.name.prefix(1) ?? "A"))
                    .font(Theme.text(15, .semibold)).foregroundStyle(.white)
                    .frame(width: 44, height: 44)
                    .background(Theme.ink, in: Circle())
            }
            .accessibilityLabel("Profile")
        }
        .padding(.horizontal, 4)
    }

    private func tipCard(_ tip: String) -> some View {
        Button { store.openCoach(prefill: "Plan tonight's dinner") } label: {
            HStack(spacing: 12) {
                Image(systemName: "sparkles")
                    .font(.system(size: 15, weight: .semibold)).foregroundStyle(Theme.ink)
                    .frame(width: 34, height: 34).background(Theme.train, in: Circle())
                Text(tip).font(Theme.text(14)).foregroundStyle(Color(hex: 0xF2F2F0))
                    .multilineTextAlignment(.leading).frame(maxWidth: .infinity, alignment: .leading)
                Text("Plan it").font(Theme.text(13, .semibold)).foregroundStyle(Theme.ink)
                    .padding(.horizontal, 12).padding(.vertical, 8)
                    .background(.white, in: RoundedRectangle(cornerRadius: 14))
            }
            .padding(.vertical, 14).padding(.leading, 16).padding(.trailing, 14)
            .background(Theme.ink, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func fuelCard(_ t: Today) -> some View {
        HStack(spacing: 18) {
            ZStack {
                Ring(progress: t.kcal.target > 0 ? t.kcal.eaten / t.kcal.target : 0)
                VStack(spacing: 0) {
                    Text(fmt(t.kcal.left)).font(Theme.mono(26)).tracking(-0.8)
                    Text("kcal left").font(Theme.text(11.5, .medium)).foregroundStyle(Theme.secondary)
                }
            }
            .frame(width: 116, height: 116)
            VStack(spacing: 11) {
                HStack(alignment: .firstTextBaseline) {
                    Text("Fuel").font(Theme.text(15, .semibold))
                    Spacer()
                    Text("\(fmt(t.kcal.eaten)) / \(fmt(t.kcal.target))").font(Theme.mono(12, .regular)).foregroundStyle(Theme.secondary)
                }
                MacroBar(label: "Protein", eaten: t.macros.protein.eaten, target: t.macros.protein.target, color: Theme.fuel)
                MacroBar(label: "Carbs", eaten: t.macros.carbs.eaten, target: t.macros.carbs.target, color: Theme.carbs)
                MacroBar(label: "Fat", eaten: t.macros.fat.eaten, target: t.macros.fat.target, color: Theme.fat)
            }
        }
        .card(22, padding: 18)
    }

    private func metrics(_ t: Today) -> some View {
        LazyVGrid(columns: [GridItem(.flexible(), spacing: 10), GridItem(.flexible())], spacing: 10) {
            MetricTile(icon: "figure.stand", title: "BMI",
                       value: t.bmi?.value.map(fmt) ?? "—", unit: nil,
                       footnote: t.bmi?.category ?? "Add height and weight")
            // ponytail: no HealthKit in the MVP, so Sleep and Resting HR are placeholders.
            MetricTile(icon: "moon", title: "Sleep", value: "—", unit: nil, footnote: "No data")
            MetricTile(icon: "heart", title: "Resting HR", value: "—", unit: "bpm", footnote: "No data")
            MetricTile(icon: "scalemass", title: "Weight", value: t.weightKg.map(fmt) ?? "—", unit: "kg", footnote: "From profile")
        }
    }

    private func weekCard(_ t: Today) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack(alignment: .firstTextBaseline) {
                Text("This week").font(Theme.text(15, .semibold))
                Spacer()
                (Text("\(t.week.sessionsDone)").font(Theme.mono(12.5)).foregroundColor(Theme.ink)
                 + Text(" of \(t.week.sessionsTarget) sessions").font(Theme.text(12.5)).foregroundColor(Theme.secondary))
            }
            WeekBars(days: t.week.days)
            if let next = t.nextWorkout {
                Divider().overlay(Theme.hairline)
                HStack(spacing: 12) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(next.name).font(Theme.text(14.5, .semibold))
                        Text("\(next.exerciseCount) exercises · about \(next.estMinutes) min")
                            .font(Theme.text(12.5)).foregroundStyle(Theme.secondary)
                    }
                    Spacer()
                    Button {
                        Task {
                            await store.startWorkout(next.id)
                            store.trainPath = [next.id]
                            store.selectedTab = .train
                        }
                    } label: {
                        Label("Start", systemImage: "play.fill").labelStyle(.titleAndIcon)
                    }
                    .buttonStyle(PillButtonStyle())
                }
            }
        }
        .card(22)
    }
}

private struct MetricTile: View {
    var icon: String
    var title: String
    var value: String
    var unit: String?
    var footnote: String

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Label(title, systemImage: icon).font(Theme.text(12.5, .medium)).foregroundStyle(Theme.secondary)
            HStack(alignment: .firstTextBaseline, spacing: 4) {
                Text(value).font(Theme.mono(22)).tracking(-0.6)
                if let unit { Text(unit).font(Theme.text(12)).foregroundStyle(Theme.secondary) }
            }
            Text(footnote).font(Theme.text(11.5)).foregroundStyle(Theme.secondary).lineLimit(1)
        }
        .card(18, padding: 14)
    }
}

/// Mon–Sun bars: orange when trained, dashed outline for today if not yet trained.
private struct WeekBars: View {
    var days: [Bool]
    private let labels = ["M", "T", "W", "T", "F", "S", "S"]
    private var todayIndex: Int { (Calendar(identifier: .gregorian).component(.weekday, from: Date()) + 5) % 7 }

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            ForEach(0..<7, id: \.self) { i in
                let done = i < days.count && days[i]
                let isToday = i == todayIndex
                VStack(spacing: 6) {
                    Group {
                        if done {
                            RoundedRectangle(cornerRadius: 6).fill(Theme.train).frame(height: 48)
                        } else if isToday {
                            RoundedRectangle(cornerRadius: 6).strokeBorder(Theme.ink, style: StrokeStyle(lineWidth: 1.5, dash: [4, 3])).frame(height: 44)
                        } else {
                            RoundedRectangle(cornerRadius: 2).fill(Color(hex: 0xECEAE6)).frame(height: 4)
                        }
                    }
                    Text(labels[i]).font(Theme.text(11, isToday ? .semibold : .regular))
                        .foregroundStyle(isToday ? Theme.ink : Theme.secondary)
                }
                .frame(maxWidth: .infinity)
            }
        }
        .frame(height: 72, alignment: .bottom)
    }
}
