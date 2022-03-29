# CREATE TABLE [dbo].[ChampSpecimenConstatEtatIntegrite](
# 	[ChampSpecimenConstatEtatIntegrite_Id] [uniqueidentifier] ROWGUIDCOL  NOT NULL,
# 	[ChampSpecimenConstatEtatIntegrite_SpecimenZoneConstatEtat_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenConstatEtatIntegrite_Integrite_Id] [uniqueidentifier] NULL,
# 	[ChampSpecimenConstatEtatIntegrite_Valeur] [nvarchar](256) NULL,
# 	[ChampSpecimenConstatEtatIntegrite_Ordre] [int] NULL,
# 	[_trackLastWriteTime] [datetime] NOT NULL,
# 	[_trackCreationTime] [datetime] NOT NULL,
# 	[_trackLastWriteUser] [nvarchar](64) NOT NULL,
# 	[_trackCreationUser] [nvarchar](64) NOT NULL,
#  CONSTRAINT [PK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_I_ChampSpecimenConstatEtatIntegrite] PRIMARY KEY NONCLUSTERED 
# (
# 	[ChampSpecimenConstatEtatIntegrite_Id] ASC
# )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, FILLFACTOR = 99, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
# ) ON [PRIMARY]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_O]  DEFAULT ((1)) FOR [ChampSpecimenConstatEtatIntegrite_Ordre]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatIntegrite__trackLastWriteTime]  DEFAULT (getdate()) FOR [_trackLastWriteTime]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] ADD  CONSTRAINT [DF_ChampSpecimenConstatEtatIntegrite__trackCreationTime]  DEFAULT (getdate()) FOR [_trackCreationTime]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_n_Reference_Id_Integrite] FOREIGN KEY([ChampSpecimenConstatEtatIntegrite_Integrite_Id])
# REFERENCES [dbo].[Integrite] ([Reference_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_n_Reference_Id_Integrite]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_n_Reference_Id_Reference] FOREIGN KEY([ChampSpecimenConstatEtatIntegrite_Integrite_Id])
# REFERENCES [dbo].[Reference] ([Reference_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_n_Reference_Id_Reference]
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite]  WITH NOCHECK ADD  CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_S_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat] FOREIGN KEY([ChampSpecimenConstatEtatIntegrite_SpecimenZoneConstatEtat_Id])
# REFERENCES [dbo].[SpecimenZoneConstatEtat] ([SpecimenZoneConstatEtat_Id])
# ALTER TABLE [dbo].[ChampSpecimenConstatEtatIntegrite] NOCHECK CONSTRAINT [FK_ChampSpecimenConstatEtatIntegrite_ChampSpecimenConstatEtatIntegrite_S_SpecimenZoneConstatEtat_Id_SpecimenZoneConstatEtat]
