using Microsoft.EntityFrameworkCore;
using Terra.Api.Models;

namespace Terra.Api.Data;

public class TerraDbContext : DbContext
{
    public TerraDbContext(DbContextOptions<TerraDbContext> options) : base(options) { }

    public DbSet<Nation> Nations => Set<Nation>();
    public DbSet<Ruler> Rulers => Set<Ruler>();
    public DbSet<TimeSnapshot> TimeSnapshots => Set<TimeSnapshot>();
    public DbSet<Territory> Territories => Set<Territory>();
    public DbSet<CumulativeTerritory> CumulativeTerritories => Set<CumulativeTerritory>();
    public DbSet<BaseMapFeature> BaseMapFeatures => Set<BaseMapFeature>();
    public DbSet<NationSnapshot> NationSnapshots => Set<NationSnapshot>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasPostgresExtension("postgis");

        modelBuilder.Entity<Nation>(entity =>
        {
            entity.ToTable("nations");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name");
            entity.Property(e => e.DisplayName).HasColumnName("display_name");
            entity.Property(e => e.Color).HasColumnName("color");
            entity.Property(e => e.WikiUrl).HasColumnName("wiki_url");
            entity.Property(e => e.FlagUrl).HasColumnName("flag_url");
            entity.Property(e => e.FoundedYear).HasColumnName("founded_year");
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");
        });

        modelBuilder.Entity<Ruler>(entity =>
        {
            entity.ToTable("rulers");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.NationId).HasColumnName("nation_id");
            entity.Property(e => e.Name).HasColumnName("name");
            entity.Property(e => e.Title).HasColumnName("title");
            entity.Property(e => e.WikiUrl).HasColumnName("wiki_url");
            entity.Property(e => e.PortraitUrl).HasColumnName("portrait_url");
            entity.Property(e => e.ReignStart).HasColumnName("reign_start");
            entity.Property(e => e.ReignEnd).HasColumnName("reign_end");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");

            entity.HasOne(e => e.Nation)
                  .WithMany(n => n.Rulers)
                  .HasForeignKey(e => e.NationId);
        });

        modelBuilder.Entity<NationSnapshot>(entity =>
        {
            entity.ToTable("nation_snapshots");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.NationId).HasColumnName("nation_id");
            entity.Property(e => e.SnapshotId).HasColumnName("snapshot_id");
            entity.Property(e => e.RulerId).HasColumnName("ruler_id");
            entity.Property(e => e.Capital).HasColumnName("capital");
            entity.Property(e => e.Language).HasColumnName("language");
            entity.Property(e => e.Religion).HasColumnName("religion");
            entity.Property(e => e.Population).HasColumnName("population");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");

            entity.HasOne(e => e.Nation)
                  .WithMany(n => n.Snapshots)
                  .HasForeignKey(e => e.NationId);

            entity.HasOne(e => e.Snapshot)
                  .WithMany(s => s.NationSnapshots)
                  .HasForeignKey(e => e.SnapshotId);

            entity.HasOne(e => e.Ruler)
                  .WithMany(r => r.NationSnapshots)
                  .HasForeignKey(e => e.RulerId);
        });

        modelBuilder.Entity<TimeSnapshot>(entity =>
        {
            entity.ToTable("time_snapshots");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Year).HasColumnName("year");
            entity.Property(e => e.Label).HasColumnName("label");
            entity.Property(e => e.Description).HasColumnName("description");
        });

        modelBuilder.Entity<Territory>(entity =>
        {
            entity.ToTable("territories");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.NationId).HasColumnName("nation_id");
            entity.Property(e => e.SnapshotId).HasColumnName("snapshot_id");
            entity.Property(e => e.Name).HasColumnName("name");
            entity.Property(e => e.Geometry).HasColumnName("geometry").HasColumnType("geometry(MultiPolygon, 4326)");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");

            entity.HasOne(e => e.Nation)
                  .WithMany(n => n.Territories)
                  .HasForeignKey(e => e.NationId);

            entity.HasOne(e => e.Snapshot)
                  .WithMany(s => s.Territories)
                  .HasForeignKey(e => e.SnapshotId);
        });

        modelBuilder.Entity<CumulativeTerritory>(entity =>
        {
            entity.ToView("cumulative_territories");
            entity.HasNoKey();
            entity.Property(e => e.SnapshotId).HasColumnName("snapshot_id");
            entity.Property(e => e.Year).HasColumnName("year");
            entity.Property(e => e.Label).HasColumnName("label");
            entity.Property(e => e.NationId).HasColumnName("nation_id");
            entity.Property(e => e.Geometry).HasColumnName("geometry").HasColumnType("geometry(MultiPolygon, 4326)");

            entity.HasOne(e => e.Nation)
                  .WithMany()
                  .HasForeignKey(e => e.NationId);
        });

        modelBuilder.Entity<BaseMapFeature>(entity =>
        {
            entity.ToTable("base_map");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.FeatureType).HasColumnName("feature_type");
            entity.Property(e => e.Name).HasColumnName("name");
            entity.Property(e => e.Geometry).HasColumnName("geometry").HasColumnType("geometry");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at");
        });
    }
}
