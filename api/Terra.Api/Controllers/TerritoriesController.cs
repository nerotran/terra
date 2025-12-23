using Microsoft.AspNetCore.Mvc;
using Terra.Api.Services;

namespace Terra.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class TerritoriesController : ControllerBase
{
    private readonly ITerritoryService _territoryService;

    public TerritoriesController(ITerritoryService territoryService)
    {
        _territoryService = territoryService;
    }

    /// <summary>
    /// Get all cumulative territories (for time slider)
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var territories = await _territoryService.GetAllTerritoriesAsync();
        return Ok(territories);
    }

    /// <summary>
    /// Get cumulative territory for a specific snapshot
    /// </summary>
    [HttpGet("{snapshotId}")]
    public async Task<IActionResult> Get(int snapshotId)
    {
        var territory = await _territoryService.GetTerritoryAsync(snapshotId);
        if (territory == null)
            return NotFound();
        return Ok(territory);
    }
}
