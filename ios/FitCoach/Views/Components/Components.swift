import SwiftUI

extension View {
    /// White rounded card used across every screen.
    func card(_ radius: CGFloat = 22, padding: CGFloat = 16) -> some View {
        self.padding(padding)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.surface, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
    }

    func screen() -> some View {
        self.background(Theme.bg.ignoresSafeArea())
    }
}

struct ScreenTitle: View {
    var title: String
    var size: CGFloat = 28
    var body: some View {
        Text(title).font(.system(size: size, weight: .bold)).tracking(-0.8).foregroundStyle(Theme.ink)
    }
}

struct Ring: View {
    var progress: Double
    var color = Theme.fuel
    var track = Theme.fuelTint2
    var lineWidth: CGFloat = 11

    var body: some View {
        ZStack {
            Circle().stroke(track, lineWidth: lineWidth)
            Circle()
                .trim(from: 0, to: min(max(progress, 0), 1))
                .stroke(color, style: StrokeStyle(lineWidth: lineWidth, lineCap: .round))
                .rotationEffect(.degrees(-90))
        }
        .padding(lineWidth / 2)
    }
}

struct Bar: View {
    var progress: Double
    var color: Color
    var track = Theme.barTrack
    var height: CGFloat = 6

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(track)
                Capsule().fill(color).frame(width: geo.size.width * min(max(progress, 0), 1))
            }
        }
        .frame(height: height)
    }
}

/// "Protein   124/160 g" over a bar (Today card).
struct MacroBar: View {
    var label: String
    var eaten: Double
    var target: Double
    var color: Color

    var body: some View {
        VStack(spacing: 5) {
            HStack {
                Text(label).font(Theme.text(12.5, .medium))
                Spacer()
                Text("\(fmt(eaten))/\(fmt(target)) g").font(Theme.mono(12, .regular)).foregroundStyle(Theme.secondary)
            }
            Bar(progress: target > 0 ? eaten / target : 0, color: color)
        }
    }
}

struct Chip: View {
    var text: String
    var body: some View {
        Text(text).font(Theme.mono(12, .regular))
            .padding(.horizontal, 8).padding(.vertical, 4)
            .background(Theme.chip, in: RoundedRectangle(cornerRadius: 8))
    }
}

/// Small tinted label ("Strength", "8 weeks").
struct Pill: View {
    var text: String
    var fg = Theme.ink
    var bg = Theme.trainTrack
    var body: some View {
        Text(text).font(Theme.text(11.5, .semibold)).foregroundStyle(fg)
            .padding(.horizontal, 8).padding(.vertical, 4)
            .background(bg, in: RoundedRectangle(cornerRadius: 8))
    }
}

/// Full-width 44pt button. Orange = training, blue = nutrition, ink = primary.
struct BigButtonStyle: ButtonStyle {
    var bg = Theme.ink
    var fg = Color.white
    var radius: CGFloat = 14
    var border: Color? = nil

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.text(14, .semibold))
            .foregroundStyle(fg)
            .frame(maxWidth: .infinity, minHeight: 44)
            .background(bg, in: RoundedRectangle(cornerRadius: radius, style: .continuous))
            .overlay { if let border { RoundedRectangle(cornerRadius: radius, style: .continuous).stroke(border, lineWidth: 1) } }
            .opacity(configuration.isPressed ? 0.7 : 1)
    }
}

/// Orange capsule ("Start", "Finish").
struct PillButtonStyle: ButtonStyle {
    var bg = Theme.train
    var fg = Theme.ink
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(Theme.text(14, .semibold))
            .foregroundStyle(fg)
            .padding(.horizontal, 18)
            .frame(minHeight: 44)
            .background(bg, in: Capsule())
            .opacity(configuration.isPressed ? 0.7 : 1)
    }
}

struct DashedRow: View {
    var text: String
    var action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Image(systemName: "bubble.left").font(.system(size: 15))
                Text(text).font(Theme.text(14, .medium))
                Spacer()
                Image(systemName: "chevron.right").font(.system(size: 13, weight: .semibold))
            }
            .foregroundStyle(Theme.tertiary)
            .padding(.horizontal, 16)
            .frame(minHeight: 56)
            .overlay(RoundedRectangle(cornerRadius: 20, style: .continuous).strokeBorder(Theme.dashed, style: StrokeStyle(lineWidth: 1.5, dash: [5, 4])))
        }
        .buttonStyle(.plain)
    }
}
