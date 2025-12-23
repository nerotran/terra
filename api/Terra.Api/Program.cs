using Microsoft.EntityFrameworkCore;
using Terra.Api.Data;
using Terra.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Database - use connection string from config, or build from env vars
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
if (string.IsNullOrEmpty(connectionString))
{
    var host = Environment.GetEnvironmentVariable("POSTGRES_HOST") ?? "localhost";
    var port = Environment.GetEnvironmentVariable("POSTGRES_PORT") ?? "5432";
    var db = Environment.GetEnvironmentVariable("POSTGRES_DB") ?? "terra";
    var user = Environment.GetEnvironmentVariable("POSTGRES_USER") ?? "terra";
    var password = Environment.GetEnvironmentVariable("POSTGRES_PASSWORD") ?? "terra_dev";
    connectionString = $"Host={host};Port={port};Database={db};Username={user};Password={password}";
}

builder.Services.AddDbContext<TerraDbContext>(options =>
    options.UseNpgsql(connectionString, o => o.UseNetTopologySuite())
);

// Services
builder.Services.AddScoped<ITerritoryService, TerritoryService>();

// CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("http://localhost:5173") // Vite dev server
              .AllowAnyHeader()
              .AllowAnyMethod();
    });
});

builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors();
app.MapControllers();

app.Run();
