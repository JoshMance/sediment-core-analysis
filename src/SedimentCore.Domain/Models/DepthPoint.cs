namespace SedimentCore.Domain.Models;

/// <summary>
/// Represents a single depth measurement point in a sediment core.
/// Pure data model - no logic.
/// </summary>
public class DepthPoint
{
    public double DepthCm { get; set; }
    public DateTime? MeasurementTime { get; set; }
    public Dictionary<string, double> Measurements { get; set; } = new();
}
