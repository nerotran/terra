using NetTopologySuite.Geometries;

namespace Terra.Api.Models;

public class Nation
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? DisplayName { get; set; }
    public string Color { get; set; } = "#8B0000";
    public string? WikiUrl { get; set; }
    public int? FoundedYear { get; set; }
    public string? FoundedEra { get; set; }
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; }

    public ICollection<Territory> Territories { get; set; } = new List<Territory>();
    public ICollection<NationSnapshot> Snapshots { get; set; } = new List<NationSnapshot>();
}

public class NationSnapshot
{
    public int Id { get; set; }
    public int NationId { get; set; }
    public int SnapshotId { get; set; }
    public string? RulerTitle { get; set; }
    public string? RulerName { get; set; }
    public string? RulerWikiUrl { get; set; }
    public int? ReignStartYear { get; set; }
    public string? ReignStartEra { get; set; }
    public int? ReignEndYear { get; set; }
    public string? ReignEndEra { get; set; }
    public string? Capital { get; set; }
    public string? Language { get; set; }
    public string? Religion { get; set; }
    public string? Population { get; set; }
    public DateTime CreatedAt { get; set; }

    public Nation Nation { get; set; } = null!;
    public TimeSnapshot Snapshot { get; set; } = null!;
}

public class TimeSnapshot
{
    public int Id { get; set; }
    public int Year { get; set; }
    public string Era { get; set; } = string.Empty; // "BC" or "AD"
    public int SortYear { get; set; }
    public string? Label { get; set; }
    public string? Description { get; set; }

    public ICollection<Territory> Territories { get; set; } = new List<Territory>();
    public ICollection<NationSnapshot> NationSnapshots { get; set; } = new List<NationSnapshot>();
}

public class Territory
{
    public int Id { get; set; }
    public int NationId { get; set; }
    public int SnapshotId { get; set; }
    public string? Name { get; set; }
    public MultiPolygon? Geometry { get; set; }
    public DateTime CreatedAt { get; set; }

    public Nation Nation { get; set; } = null!;
    public TimeSnapshot Snapshot { get; set; } = null!;
}

public class CumulativeTerritory
{
    public int SnapshotId { get; set; }
    public int Year { get; set; }
    public string Era { get; set; } = string.Empty;
    public int SortYear { get; set; }
    public string? Label { get; set; }
    public int NationId { get; set; }
    public MultiPolygon? Geometry { get; set; }

    public Nation Nation { get; set; } = null!;
}

public class BaseMapFeature
{
    public int Id { get; set; }
    public string FeatureType { get; set; } = string.Empty;
    public string? Name { get; set; }
    public Geometry? Geometry { get; set; }
    public DateTime CreatedAt { get; set; }
}
