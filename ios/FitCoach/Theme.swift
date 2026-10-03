import SwiftUI

enum Theme {
    static let bg = Color(hex: 0xF5F5F2)
    static let surface = Color.white
    static let ink = Color(hex: 0x111214)
    static let secondary = Color(hex: 0x5E636C)
    static let tertiary = Color(hex: 0x3A3D43)
    static let hairline = Color(hex: 0xF0EFEC)
    static let border = Color(hex: 0xDAD8D2)
    static let train = Color(hex: 0xF25C1F)
    static let trainTint = Color(hex: 0xFFF1EA)
    static let trainTrack = Color(hex: 0xF1EEEA)
    static let fuel = Color(hex: 0x2E64E8)
    static let fuelDeep = Color(hex: 0x2450BF)
    static let carbs = Color(hex: 0x8FB0F5)
    static let fat = Color(hex: 0xA3A8B0)
    static let fuelTint = Color(hex: 0xF1F4FB)
    static let fuelTint2 = Color(hex: 0xE8EDF8)
    static let barTrack = Color(hex: 0xEEF0F4)
    static let chip = Color(hex: 0xF3F4F7)
    static let field = Color(hex: 0xF1F0ED)
    static let dashed = Color(hex: 0xC9C7C1)

    static func mono(_ size: CGFloat, _ weight: Font.Weight = .semibold) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }
    static func text(_ size: CGFloat, _ weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight)
    }
}

extension Color {
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xFF) / 255, green: Double((hex >> 8) & 0xFF) / 255, blue: Double(hex & 0xFF) / 255)
    }
}

/// 1620 -> "1,620", 74.6 -> "74.6", 75.0 -> "75"
func fmt(_ v: Double) -> String { v.formatted(.number.precision(.fractionLength(0...1))) }
