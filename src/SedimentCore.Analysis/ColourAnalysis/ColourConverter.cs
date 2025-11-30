using SedimentCore.Domain.Models;

namespace SedimentCore.Analysis.ColourAnalysis;

/// <summary>
/// Provides colour space conversion algorithms.
/// Single source of truth for RGB to Lab, HSV, etc.
/// </summary>
public class ColourConverter
{
    /// <summary>
    /// Converts RGB to CIE Lab colour space.
    /// </summary>
    public static (double L, double a, double b) RgbToLab(byte r, byte g, byte b)
    {
        // TODO: Implement proper RGB to Lab conversion
        // This is a placeholder
        return (0, 0, 0);
    }

    /// <summary>
    /// Converts RGB to HSV colour space.
    /// </summary>
    public static (double H, double S, double V) RgbToHsv(byte r, byte g, byte b)
    {
        // TODO: Implement proper RGB to HSV conversion
        // This is a placeholder
        return (0, 0, 0);
    }

    /// <summary>
    /// Enriches a colour profile with Lab values.
    /// </summary>
    public static ColourProfile EnrichWithLab(ColourProfile profile)
    {
        var (l, a, b) = RgbToLab(profile.R, profile.G, profile.B);
        profile.L = l;
        profile.a = a;
        profile.b = b;
        return profile;
    }
}
