using NetTopologySuite.Geometries;

namespace Terra.Api.Models;

public class Nation
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? DisplayName { get; set; }
    public string Color { get; set; } = "#8B0000";
    public DateTime CreatedAt { get; set; }

    public ICollection<Territory> Territories { get; set; } = new List<Territory>();
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
    public string? Color { get; set; }
    public MultiPolygon? Geometry { get; set; }
}

public class BaseMapFeature
{
    public int Id { get; set; }
    public string FeatureType { get; set; } = string.Empty;
    public string? Name { get; set; }
    public Geometry? Geometry { get; set; }
    public DateTime CreatedAt { get; set; }
}
