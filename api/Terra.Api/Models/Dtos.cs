using System.Text.Json.Serialization;

namespace Terra.Api.Models;

public class SnapshotDto
{
    [JsonPropertyName("snapshot_id")]
    public int SnapshotId { get; set; }
    
    [JsonPropertyName("year")]
    public int Year { get; set; }
    
    [JsonPropertyName("era")]
    public string Era { get; set; } = string.Empty;
    
    [JsonPropertyName("sort_year")]
    public int SortYear { get; set; }
    
    [JsonPropertyName("label")]
    public string? Label { get; set; }
}

public class TerritoryDto
{
    [JsonPropertyName("snapshot_id")]
    public int SnapshotId { get; set; }

    [JsonPropertyName("year")]
    public int Year { get; set; }

    [JsonPropertyName("era")]
    public string Era { get; set; } = string.Empty;

    [JsonPropertyName("sort_year")]
    public int SortYear { get; set; }

    [JsonPropertyName("label")]
    public string? Label { get; set; }

    [JsonPropertyName("color")]
    public string? Color { get; set; }

    [JsonPropertyName("geometry")]
    public object? Geometry { get; set; } // GeoJSON object
}

public class BaseMapDto
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "FeatureCollection";

    [JsonPropertyName("features")]
    public List<BaseMapFeatureDto> Features { get; set; } = new();
}

public class BaseMapFeatureDto
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = "Feature";

    [JsonPropertyName("properties")]
    public object Properties { get; set; } = new { };

    [JsonPropertyName("geometry")]
    public object? Geometry { get; set; }
}
