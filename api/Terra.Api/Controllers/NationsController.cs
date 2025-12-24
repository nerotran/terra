using Microsoft.AspNetCore.Mvc;
using Terra.Api.Services;

namespace Terra.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class NationsController : ControllerBase
{
    private readonly ITerritoryService _territoryService;

    public NationsController(ITerritoryService territoryService)
    {
        _territoryService = territoryService;
    }

    /// <summary>
    /// Get nation details for a specific time snapshot
    /// </summary>
    [HttpGet("{nationId}/snapshot/{snapshotId}")]
    public async Task<IActionResult> GetDetails(int nationId, int snapshotId)
    {
        var details = await _territoryService.GetNationDetailsAsync(nationId, snapshotId);
        if (details == null)
            return NotFound();
        return Ok(details);
    }
}
