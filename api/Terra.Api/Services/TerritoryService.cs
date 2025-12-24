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
            .OrderBy(s => s.SortYear)
            .Select(s => new SnapshotDto
            {
                SnapshotId = s.Id,
                Year = s.Year,
                Era = s.Era,
                SortYear = s.SortYear,
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
            Era = t.Era,
            SortYear = t.SortYear,
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
            .OrderBy(t => t.SortYear)
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

        // Get time-specific snapshot data (find closest snapshot <= requested)
        var snapshot = await _db.NationSnapshots
            .Include(ns => ns.Snapshot)
            .Where(ns => ns.NationId == nationId && ns.Snapshot.Id <= snapshotId)
            .OrderByDescending(ns => ns.Snapshot.SortYear)
            .FirstOrDefaultAsync();

        var dto = new NationDetailsDto
        {
            Id = nation.Id,
            Name = nation.Name,
            DisplayName = nation.DisplayName,
            Color = nation.Color,
            WikiUrl = nation.WikiUrl,
            Founded = FormatYear(nation.FoundedYear, nation.FoundedEra),
            Description = nation.Description
        };

        if (snapshot != null)
        {
            dto.RulerTitle = snapshot.RulerTitle;
            dto.RulerName = snapshot.RulerName;
            dto.RulerWikiUrl = snapshot.RulerWikiUrl;
            dto.ReignStart = FormatYear(snapshot.ReignStartYear, snapshot.ReignStartEra);
            dto.ReignEnd = FormatYear(snapshot.ReignEndYear, snapshot.ReignEndEra);
            dto.Capital = snapshot.Capital;
            dto.Language = snapshot.Language;
            dto.Religion = snapshot.Religion;
            dto.Population = snapshot.Population;
        }

        return dto;
    }

    private static string? FormatYear(int? year, string? era)
    {
        if (year == null) return null;
        return $"{year} {era ?? "AD"}";
    }
}
