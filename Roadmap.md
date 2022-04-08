1. Transformers for Callers/Readers/Writers that take mimic the Grasshopper toolset for Reading. Accounts/Streams/Objects
    
    Essentially all implemented as python scripts. Each starts with a Reader class that the Caller transformer hooks onto, processes and returns.
    - [x] StreamReader - Uses the installed default account from Speckle Manager and a url. Resolves to Stream, Branches, Commits and Objects depending on the root.
    - [x] GetDefaultClient - returns a feature with the default client attributes
    - [x] GetStreams - returns streams available to the authenticated client
    - [x] GetBranches - returns branches available within the given stream(s)
    - [x] GetLatest - returns the latest commit on Main branch and resolves commit objects to features
    - [ ] GetObject

2. Wrap the logic and “options” as Custom Transformers to make usability better
    
    - [x] SpeckleClient - Builds an authenticated client (?) to use as an override to the default. Uses tokens.

3. Expand conversions incrementally.
4. FME Speckle Writer
5. Delve into the Reader/Writer options for FME to match the other Connectors (ish)
