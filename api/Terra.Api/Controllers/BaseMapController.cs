using Microsoft.AspNetCore.Mvc;
using Terra.Api.Services;

namespace Terra.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class BaseMapController : ControllerBase
{
    private readonly ITerritoryService _territoryService;

    public BaseMapController(ITerritoryService territoryService)
    {
        _territoryService = territoryService;
    }

    /// <summary>
    /// Get base map features (land, lakes, etc.)
    /// </summary>
    [HttpGet("{featureType}")]
    public async Task<IActionResult> Get(string featureType = "land")
    {
        var baseMap = await _territoryService.GetBaseMapAsync(featureType);
        return Ok(baseMap);
    }
}
