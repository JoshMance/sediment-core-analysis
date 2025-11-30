namespace SedimentCore.Domain.Models;

/// <summary>
/// Represents a colour measurement at a specific depth.
/// Pure data model - no conversion or analysis logic.
/// </summary>
public class ColourProfile
{
    public double DepthCm { get; set; }

    // RGB values (0-255)
    public byte R { get; set; }
    public byte G { get; set; }
    public byte B { get; set; }

    // Alternative colour spaces can be calculated by Analysis project
    public double? L { get; set; }  // Lab L* (optional, computed)
    public double? a { get; set; }  // Lab a* (optional, computed)
    public double? b { get; set; }  // Lab b* (optional, computed)
}
