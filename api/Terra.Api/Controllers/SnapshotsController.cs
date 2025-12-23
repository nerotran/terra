using Microsoft.AspNetCore.Mvc;
using Terra.Api.Services;

namespace Terra.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class SnapshotsController : ControllerBase
{
    private readonly ITerritoryService _territoryService;

    public SnapshotsController(ITerritoryService territoryService)
    {
        _territoryService = territoryService;
    }

    /// <summary>
    /// Get all time snapshots (for populating time slider)
    /// </summary>
    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var snapshots = await _territoryService.GetSnapshotsAsync();
        return Ok(snapshots);
    }
}
