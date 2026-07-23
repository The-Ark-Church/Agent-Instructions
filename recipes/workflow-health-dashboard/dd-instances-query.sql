-- Workflow Health instances grid (classic Dynamic Data block).
-- Params bound from the query string via the block's Query Params setting:
--   WorkflowTypeId, MinAgeDays (ints, 0 = ignore), StuckOnly (bool), Person (PersonAlias Guid
--   from the Page Parameter Filter person picker; matches workflows the person INITIATED or
--   is currently ASSIGNED to via an open activity — any of the person's aliases).
-- GETDATE() here is UTC (Azure SQL); day-level ages can skew up to 6 hours around midnight,
-- which is acceptable for this grid. The workflow-health endpoints use RockDateTime instead.
DECLARE @TypeIdInt INT = ISNULL(TRY_CAST(@WorkflowTypeId AS INT), 0)
DECLARE @MinAgeInt INT = ISNULL(TRY_CAST(@MinAgeDays AS INT), 0)
DECLARE @StuckBit BIT = CASE WHEN @StuckOnly IN ('1', 'True', 'true', 'Yes') THEN 1 ELSE 0 END
DECLARE @FilterPersonId INT = ISNULL((SELECT TOP 1 [fpa].[PersonId] FROM [PersonAlias] AS [fpa] WHERE [fpa].[Guid] = TRY_CAST(@Person AS UNIQUEIDENTIFIER)), 0)

SELECT TOP 1000
  [w].[Id],
  [wt].[Name] AS [Workflow Type],
  ISNULL([w].[Name], '') AS [Instance],
  [w].[Status],
  DATEDIFF(DAY, [w].[ActivatedDateTime], GETDATE()) AS [Age Days],
  [w].[ActivatedDateTime] AS [Activated],
  [w].[LastProcessedDateTime] AS [Last Processed],
  CASE WHEN [w].[IsProcessing] = 1 AND ([w].[LastProcessedDateTime] IS NULL OR [w].[LastProcessedDateTime] < DATEADD(HOUR, -1, GETDATE())) THEN 'Yes' ELSE '' END AS [Stuck],
  ISNULL([p].[NickName] + ' ' + [p].[LastName], '') AS [Initiator],
  ISNULL((SELECT TOP 1 ISNULL([ap].[NickName] + ' ' + [ap].[LastName], [ag].[Name])
          FROM [WorkflowActivity] AS [wa2]
          LEFT JOIN [PersonAlias] AS [apa] ON [apa].[Id] = [wa2].[AssignedPersonAliasId]
          LEFT JOIN [Person] AS [ap] ON [ap].[Id] = [apa].[PersonId]
          LEFT JOIN [Group] AS [ag] ON [ag].[Id] = [wa2].[AssignedGroupId]
          WHERE [wa2].[WorkflowId] = [w].[Id] AND [wa2].[CompletedDateTime] IS NULL
          ORDER BY [wa2].[ActivatedDateTime] DESC), '') AS [Assigned To]
FROM [Workflow] AS [w]
JOIN [WorkflowType] AS [wt] ON [wt].[Id] = [w].[WorkflowTypeId]
LEFT JOIN [PersonAlias] AS [pa] ON [pa].[Id] = [w].[InitiatorPersonAliasId]
LEFT JOIN [Person] AS [p] ON [p].[Id] = [pa].[PersonId]
WHERE [w].[CompletedDateTime] IS NULL
  AND (@TypeIdInt = 0 OR [w].[WorkflowTypeId] = @TypeIdInt)
  AND (@MinAgeInt = 0 OR [w].[ActivatedDateTime] < DATEADD(DAY, -@MinAgeInt, GETDATE()))
  AND (@StuckBit = 0 OR ([w].[IsProcessing] = 1 AND ([w].[LastProcessedDateTime] IS NULL OR [w].[LastProcessedDateTime] < DATEADD(HOUR, -1, GETDATE()))))
  AND (@FilterPersonId = 0
       OR [w].[InitiatorPersonAliasId] IN (SELECT [pa2].[Id] FROM [PersonAlias] AS [pa2] WHERE [pa2].[PersonId] = @FilterPersonId)
       OR EXISTS (SELECT 1 FROM [WorkflowActivity] AS [waP]
                  WHERE [waP].[WorkflowId] = [w].[Id] AND [waP].[CompletedDateTime] IS NULL
                    AND [waP].[AssignedPersonAliasId] IN (SELECT [pa3].[Id] FROM [PersonAlias] AS [pa3] WHERE [pa3].[PersonId] = @FilterPersonId)))
ORDER BY [w].[ActivatedDateTime] ASC
