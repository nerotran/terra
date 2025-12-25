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

    [JsonPropertyName("wiki_url")]
    public string? WikiUrl { get; set; }
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

    [JsonPropertyName("founded")]
    public string? Founded { get; set; }

    [JsonPropertyName("description")]
    public string? Description { get; set; }

    // Time-specific data from nation_snapshots
    [JsonPropertyName("ruler_title")]
    public string? RulerTitle { get; set; }

    [JsonPropertyName("ruler_name")]
    public string? RulerName { get; set; }

    [JsonPropertyName("ruler_wiki_url")]
    public string? RulerWikiUrl { get; set; }

    [JsonPropertyName("ruler_portrait_url")]
    public string? RulerPortraitUrl { get; set; }

    [JsonPropertyName("reign_start")]
    public string? ReignStart { get; set; }

    [JsonPropertyName("reign_end")]
    public string? ReignEnd { get; set; }

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
