using System.Text.Json.Serialization;

namespace Terra.Api.Models;

public class SnapshotDto
{
    [JsonPropertyName("snapshot_id")]
    public int SnapshotId { get; set; }

    [JsonPropertyName("year")]
    public int Year { get; set; }  // Signed: negative for BC, positive for AD

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

    [JsonPropertyName("wiki_url")]
    public string? WikiUrl { get; set; }
}

public class RulerDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string? Title { get; set; }

    [JsonPropertyName("wiki_url")]
    public string? WikiUrl { get; set; }

    [JsonPropertyName("portrait_url")]
    public string? PortraitUrl { get; set; }

    [JsonPropertyName("reign_start")]
    public int ReignStart { get; set; }  // Signed year

    [JsonPropertyName("reign_end")]
    public int? ReignEnd { get; set; }  // Signed year, null if still reigning
}

public class NationDetailsDto
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("display_name")]
    public string? DisplayName { get; set; }

    [JsonPropertyName("color")]
    public string Color { get; set; } = "#8B0000";

    [JsonPropertyName("wiki_url")]
    public string? WikiUrl { get; set; }

    [JsonPropertyName("flag_url")]
    public string? FlagUrl { get; set; }

    [JsonPropertyName("founded_year")]
    public int? FoundedYear { get; set; }  // Signed year

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    // Current ruler for the snapshot
    [JsonPropertyName("ruler")]
    public RulerDto? Ruler { get; set; }

    // Time-specific data from nation_snapshots
    [JsonPropertyName("capital")]
    public string? Capital { get; set; }

    [JsonPropertyName("language")]
    public string? Language { get; set; }

    [JsonPropertyName("religion")]
    public string? Religion { get; set; }

    [JsonPropertyName("population")]
    public string? Population { get; set; }
}

public class TerritoryDto
{
    [JsonPropertyName("snapshot_id")]
    public int SnapshotId { get; set; }

    [JsonPropertyName("year")]
    public int Year { get; set; }  // Signed: negative for BC, positive for AD

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
