using Microsoft.EntityFrameworkCore;
using NetTopologySuite.IO;
using Terra.Api.Data;
using Terra.Api.Models;

namespace Terra.Api.Services;

public interface ITerritoryService
{
    Task<List<SnapshotDto>> GetSnapshotsAsync();
    Task<TerritoryDto?> GetTerritoryAsync(int snapshotId);
    Task<List<TerritoryDto>> GetAllTerritoriesAsync();
    Task<BaseMapDto> GetBaseMapAsync(string featureType = "land");
    Task<NationDetailsDto?> GetNationDetailsAsync(int nationId, int snapshotId);
}

public class TerritoryService : ITerritoryService
{
    private readonly TerraDbContext _db;
    private readonly GeoJsonWriter _geoJsonWriter;

    public TerritoryService(TerraDbContext db)
    {
        _db = db;
        _geoJsonWriter = new GeoJsonWriter();
    }

    public async Task<List<SnapshotDto>> GetSnapshotsAsync()
    {
        return await _db.TimeSnapshots
            .OrderBy(s => s.Year)
            .Select(s => new SnapshotDto
            {
                SnapshotId = s.Id,
                Year = s.Year,
                Label = s.Label
            })
            .ToListAsync();
    }

    public async Task<TerritoryDto?> GetTerritoryAsync(int snapshotId)
    {
        var territory = await _db.CumulativeTerritories
            .Include(t => t.Nation)
            .Where(t => t.SnapshotId == snapshotId)
            .FirstOrDefaultAsync();

        if (territory == null) return null;

        return MapToDto(territory);
    }

    private TerritoryDto MapToDto(CumulativeTerritory t)
    {
        return new TerritoryDto
        {
            SnapshotId = t.SnapshotId,
            Year = t.Year,
            Label = t.Label,
            Nation = new NationDto
            {
                Id = t.Nation.Id,
                Name = t.Nation.Name,
                DisplayName = t.Nation.DisplayName,
                Color = t.Nation.Color,
                WikiUrl = t.Nation.WikiUrl
            },
            Geometry = t.Geometry != null
                ? System.Text.Json.JsonSerializer.Deserialize<object>(_geoJsonWriter.Write(t.Geometry))
                : null
        };
    }

    public async Task<List<TerritoryDto>> GetAllTerritoriesAsync()
    {
        var territories = await _db.CumulativeTerritories
            .Include(t => t.Nation)
            .OrderBy(t => t.Year)
            .ToListAsync();

        return territories.Select(MapToDto).ToList();
    }

    public async Task<BaseMapDto> GetBaseMapAsync(string featureType = "land")
    {
        var features = await _db.BaseMapFeatures
            .Where(f => f.FeatureType == featureType)
            .ToListAsync();

        return new BaseMapDto
        {
            Features = features.Select(f => new BaseMapFeatureDto
            {
                Geometry = f.Geometry != null
                    ? System.Text.Json.JsonSerializer.Deserialize<object>(_geoJsonWriter.Write(f.Geometry))
                    : null
            }).ToList()
        };
    }

    public async Task<NationDetailsDto?> GetNationDetailsAsync(int nationId, int snapshotId)
    {
        var nation = await _db.Nations.FindAsync(nationId);
        if (nation == null) return null;

        // Get the requested snapshot to find its year
        var requestedSnapshot = await _db.TimeSnapshots.FindAsync(snapshotId);
        if (requestedSnapshot == null) return null;

        // Get time-specific snapshot data (find closest snapshot <= requested year)
        var snapshot = await _db.NationSnapshots
            .Include(ns => ns.Snapshot)
            .Include(ns => ns.Ruler)
            .Where(ns => ns.NationId == nationId && ns.Snapshot.Year <= requestedSnapshot.Year)
            .OrderByDescending(ns => ns.Snapshot.Year)
            .FirstOrDefaultAsync();

        var dto = new NationDetailsDto
        {
            Id = nation.Id,
            Name = nation.Name,
            DisplayName = nation.DisplayName,
            Color = nation.Color,
            WikiUrl = nation.WikiUrl,
            FlagUrl = nation.FlagUrl,
            FoundedYear = nation.FoundedYear,
            Description = nation.Description
        };

        if (snapshot != null)
        {
            dto.Capital = snapshot.Capital;
            dto.Language = snapshot.Language;
            dto.Religion = snapshot.Religion;
            dto.Population = snapshot.Population;

            if (snapshot.Ruler != null)
            {
                dto.Ruler = new RulerDto
                {
                    Id = snapshot.Ruler.Id,
                    Name = snapshot.Ruler.Name,
                    Title = snapshot.Ruler.Title,
                    WikiUrl = snapshot.Ruler.WikiUrl,
                    PortraitUrl = snapshot.Ruler.PortraitUrl,
                    ReignStart = snapshot.Ruler.ReignStart,
                    ReignEnd = snapshot.Ruler.ReignEnd
                };
            }
        }

        return dto;
    }
}
