using NetTopologySuite.Geometries;

namespace Terra.Api.Models;

public class Nation
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? DisplayName { get; set; }
    public string Color { get; set; } = "#8B0000";
    public string? WikiUrl { get; set; }
    public string? FlagUrl { get; set; }
    public int? FoundedYear { get; set; }  // Signed: negative for BC, positive for AD
    public string? Description { get; set; }
    public DateTime CreatedAt { get; set; }

    public ICollection<Territory> Territories { get; set; } = new List<Territory>();
    public ICollection<NationSnapshot> Snapshots { get; set; } = new List<NationSnapshot>();
    public ICollection<Ruler> Rulers { get; set; } = new List<Ruler>();
}

public class Ruler
{
    public int Id { get; set; }
    public int NationId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Title { get; set; }
    public string? WikiUrl { get; set; }
    public string? PortraitUrl { get; set; }
    public int ReignStart { get; set; }  // Signed: negative for BC, positive for AD
    public int? ReignEnd { get; set; }  // Signed: null if still reigning
    public DateTime CreatedAt { get; set; }

    public Nation Nation { get; set; } = null!;
    public ICollection<NationSnapshot> NationSnapshots { get; set; } = new List<NationSnapshot>();
}

public class NationSnapshot
{
    public int Id { get; set; }
    public int NationId { get; set; }
    public int SnapshotId { get; set; }
    public int? RulerId { get; set; }
    public string? Capital { get; set; }
    public string? Language { get; set; }
    public string? Religion { get; set; }
    public string? Population { get; set; }
    public DateTime CreatedAt { get; set; }

    public Nation Nation { get; set; } = null!;
    public TimeSnapshot Snapshot { get; set; } = null!;
    public Ruler? Ruler { get; set; }
}

public class TimeSnapshot
{
    public int Id { get; set; }
    public int Year { get; set; }  // Signed: negative for BC, positive for AD
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
    public int Year { get; set; }  // Signed: negative for BC, positive for AD
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
