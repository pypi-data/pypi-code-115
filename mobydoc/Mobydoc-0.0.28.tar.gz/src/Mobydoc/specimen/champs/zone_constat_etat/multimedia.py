# CREATE TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia](
# 	[ChampSpecimenZoneConstatEtatMultimedia_Id] [uniqueidentifier] ROWGUIDCOL  NOT NULL,
# 	[ChampSpecimenZoneConstatEtatMultimedia_SpecimenZoneConstatEtat_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenZoneConstatEtatMultimedia_Multimedia_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenZoneConstatEtatMultimedia_Ordre] [int] NULL,
# 	[_trackLastWriteTime] [datetime] NOT NULL,
# 	[_trackCreationTime] [datetime] NOT NULL,
# 	[_trackLastWriteUser] [nvarchar](64) NOT NULL,
# 	[_trackCreationUser] [nvarchar](64) NOT NULL,
#  CONSTRAINT [PK_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultime] PRIMARY KEY NONCLUSTERED 
# (
# 	[ChampSpecimenZoneConstatEtatMultimedia_Id] ASC
# )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, FILLFACTOR = 99, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
# ) ON [PRIMARY]
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia] ADD  CONSTRAINT [DF_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultimd]  DEFAULT ((1)) FOR [ChampSpecimenZoneConstatEtatMultimedia_Ordre]
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia] ADD  CONSTRAINT [DF_ChampSpecimenZoneConstatEtatMultime__trackLastWriteTime]  DEFAULT (getdate()) FOR [_trackLastWriteTime]
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia] ADD  CONSTRAINT [DF_ChampSpecimenZoneConstatEtatMultime__trackCreationTime]  DEFAULT (getdate()) FOR [_trackCreationTime]
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultima_Multimedia_Id_Multimedia] FOREIGN KEY([ChampSpecimenZoneConstatEtatMultimedia_Multimedia_Id])
# REFERENCES [dbo].[Multimedia] ([Multimedia_Id])
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia] NOCHECK CONSTRAINT [FK_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultima_Multimedia_Id_Multimedia]
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultimi_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat] FOREIGN KEY([ChampSpecimenZoneConstatEtatMultimedia_SpecimenZoneConstatEtat_Id])
# REFERENCES [dbo].[SpecimenZoneConstatEtat] ([SpecimenZoneConstatEtat_Id])
# ALTER TABLE [dbo].[ChampSpecimenZoneConstatEtatMultimedia] NOCHECK CONSTRAINT [FK_ChampSpecimenZoneConstatEtatMultime_ChampSpecimenZoneConstatEtatMultimi_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat]
