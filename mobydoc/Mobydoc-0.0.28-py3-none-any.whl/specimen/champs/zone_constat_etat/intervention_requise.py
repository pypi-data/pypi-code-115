# CREATE TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise](
# 	[ChampSpecimenConstatEtatInterventionRequise_Id] [uniqueidentifier] ROWGUIDCOL  NOT NULL,
# 	[ChampSpecimenConstatEtatInterventionRequise_SpecimenZoneConstatEtat_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenConstatEtatInterventionRequise_InterventionRequise_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenConstatEtatInterventionRequise_Valeur] [nvarchar](256) NULL,
# 	[ChampSpecimenConstatEtatInterventionRequise_Ordre] [int] NULL,
# 	[_trackLastWriteTime] [datetime] NOT NULL,
# 	[_trackCreationTime] [datetime] NOT NULL,
# 	[_trackLastWriteUser] [nvarchar](64) NOT NULL,
# 	[_trackCreationUser] [nvarchar](64) NOT NULL,
#  CONSTRAINT [PK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventio] PRIMARY KEY NONCLUSTERED 
# (
# 	[ChampSpecimenConstatEtatInterventionRequise_Id] ASC
# )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, FILLFACTOR = 99, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
# ) ON [PRIMARY]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventiR]  DEFAULT ((1)) FOR [ChampSpecimenConstatEtatInterventionRequise_Ordre]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatInterventio__trackLastWriteTime]  DEFAULT (getdate()) FOR [_trackLastWriteTime]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatInterventio__trackCreationTime]  DEFAULT (getdate()) FOR [_trackCreationTime]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventie_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat] FOREIGN KEY([ChampSpecimenConstatEtatInterventionRequise_SpecimenZoneConstatEtat_Id])
# REFERENCES [dbo].[SpecimenZoneConstatEtat] ([SpecimenZoneConstatEtat_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventie_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventiq_Reference_Id_Reference] FOREIGN KEY([ChampSpecimenConstatEtatInterventionRequise_InterventionRequise_Id])
# REFERENCES [dbo].[Reference] ([Reference_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventiq_Reference_Id_Reference]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventiq_Reference_Id_TypeIntervention] FOREIGN KEY([ChampSpecimenConstatEtatInterventionRequise_InterventionRequise_Id])
# REFERENCES [dbo].[TypeIntervention] ([Reference_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatInterventionRequise] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatInterventio_ChampSpecimenConstatEtatInterventiq_Reference_Id_TypeIntervention]
