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
                Color = t.Nation.Color
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
}
