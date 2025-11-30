namespace SedimentCore.Domain.Models;

/// <summary>
/// Represents metadata for a sediment core sample.
/// Pure data model - no logic.
/// </summary>
public class CoreMetadata
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Location { get; set; } = string.Empty;
    public DateTime CollectionDate { get; set; }
    public double TotalDepthCm { get; set; }
    public string Collector { get; set; } = string.Empty;
    public Dictionary<string, string> CustomProperties { get; set; } = new();
}
