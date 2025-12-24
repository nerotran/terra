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

public class NationDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("display_name")]
    public string? DisplayName { get; set; }

    [JsonPropertyName("color")]
    public string Color { get; set; } = "#8B0000";
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

    [JsonPropertyName("nation")]
    public NationDto Nation { get; set; } = null!;

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
