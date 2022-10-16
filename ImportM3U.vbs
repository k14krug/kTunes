' =========
' ImportM3U
' =========
' Version 1.0.0.9 - March 29th 2014
' Copyright © Steve MacGuire 2011-2014
' http://samsoft.org.uk/iTunes/ImportM3U.vbs
' Please visit http://samsoft.org.uk/iTunes/scripts.asp for updates

' =======
' Licence
' =======
' This program is free software: you can redistribute it and/or modify it under the terms
' of the GNU General Public License as published by the Free Software Foundation, either
' version 3 of the License, or (at your option) any later version.

' This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
' without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
' See the GNU General Public License for more details.

' Please visit http://www.gnu.org/licenses/gpl-3.0-standalone.html to view the GNU GPLv3 licence.

' ===========
' Description
' ===========
' Imports an .m3u playlist into iTunes

' =========
' ChangeLog
' =========
' Version 1.0.0.1 - Initial version
' Version 1.0.0.2 - Update to process WMA tracks
' Version 1.0.0.3 - Update to work relative file references and ignore non-existent tracks\bad paths
' Version 1.0.0.4 - Update for path relative to root of drive or network share paths
' Version 1.0.0.5 - Updated to new common code base with progress bar
' Version 1.0.0.6 - Updated to support m3u8 files - nix now a work in progress
' Version 1.0.0.7 - Updated for possible trip up in ProgressBar class
' Version 1.0.0.8 - Updated to support UTF-8 encoding
' Version 1.0.0.9 - Allow a named file to be imported



' ==========
' To-do List
' ==========
' Add more things to do

' =============================
' Declare constants & variables
' =============================
Option Explicit
Dim Intro,Outro,Check   ' Confirmation and reporing
Dim PB,Prog,Debug       ' Control the progress bar
Dim Clock,T1,T2,Timing  ' The secret of great comedy
Dim iTunes              ' Handle to iTunes application
Dim Count               ' The number of tracks
Dim B,P,S               ' Counters
Dim nl,tab              ' New line/tab strings
Dim Quit                ' Used to abort script

Const Title="Import M3U"
Const Summary="Drag an M3U file onto this script to add it to your iTunes library."

Dim Drive               ' A drivespec
Dim FilePath            ' Path of file to import
Dim Folder              ' Folder containing playlist
Dim FSO                 ' Handle to FileSystemObject
Dim Playlist            ' Playlist to add files to
Dim U                   ' Indicates Unicode input file

' =======================
' Initialise user options
' =======================
Intro=True              ' Set false to skip initial prompts, avoid if non-reversible actions
Outro=True              ' Produce summary report
Check=True              ' Track-by-track confirmation
Prog=True               ' Display progress bar
Debug=True              ' Include any debug messages in progress bar
Timing=True             ' Display running time
FilePath=""             ' Edit this to use a specific file instead of drag & drop.


' ============
' Main program
' ============

Init                    ' Set things up
Action                  ' Main process 
Results                 ' Summary

  ' ===================
' End of main program
' ===================


' ===============================
' Declare subroutines & functions
' ===============================


' Note: The bulk of the code in this script is concerned with making sure that only suitable tracks are processed by
'       the following module and supporting numerous options for track selection, confirmation, progress and results.


' Loop through the input file
' Modified 2013-08-21
Sub Action
  Dim ADO,C,F,File,I,Line,List,N,R,T,W,WMA
  F=True
  C=0
  I=0
    
  ' Pass 1 - Count the number of potential tracks to add
  Set ADO=CreateObject("Adodb.Stream")
  With ADO
    .CharSet="UTF-8"
    .Type=2
    .Open
    .LoadFromFile FilePath
    Do While Not ADO.EOS
      Line=Trim(.ReadText(-2))
      If Line<>"" And Left(Line,1)<>"#" Then
        ' If Prog Then PB.Step True
        C=C+1
        If LCase(Right(Line,4))=".wma" Then W=W+1
      End If
    Loop
  End With
  Set ADO=Nothing 
    
' Confirmation dialogs
  If C=0 Then
    T="The playlist file " & Playlist & ".m3u contains no entires!"
    T=T & nl & nl & "No playlist has been created."
    MsgBox T,vbExclamation,Title
    WScript.Quit
  ElseIf Intro Then
    If W>0 Then
      T="Create a playlist called """ & Playlist & """ and add "
      T=T & C & " item" & Plural(C,"s","") & " to it." & nl
      T=T & "N.B. " & W & Plural(W," entries are "," entry is ") & "in WMA format." & nl & nl
      T=T & "Convert and add the WMA file" & Plural(W,"s","") & " using the current iTunes import settings?"
      R=MsgBox(T,vbYesNoCancel+vbQuestion,Title)
      If R=vbCancel Then WScript.Quit
      If R=vbNo Then
        If W=C Then
          T="The playlist file " & Playlist & ".m3u only contains WMA entries which are being skipped!"
          T=T & nl & nl & "No playlist has been created."
          MsgBox T,vbExclamation,Title
          WScript.Quit
        End If
        F=False
      End If
    Else
      T="Create a playlist called """ & Playlist & """ and add "
      T=T & C & " item" & Plural(C,"s","") & " to it?"
      R=MsgBox(T,vbOKCancel+vbQuestion,Title)
      If R<>vbOK Then WScript.Quit
    End If
  End If

  Count=C  
  If Prog Then                  ' Create ProgessBar
    Set PB=New ProgBar
    PB.Show
  End If
  Clock=0 : StartTimer

  ' Pass 2 - Add the tracks to the playlist
  Set ADO=CreateObject("Adodb.Stream")
  With ADO
    .CharSet="UTF-8"
    .Type=2
    .Open
    .LoadFromFile FilePath
    Do While Not ADO.EOS
      Line=Trim(.ReadText(-2))
      If Line<>"" And Left(Line,1)<>"#" Then
        I=I+1                 
        If Prog Then
          PB.SetStatus Status(I)
          PB.Progress I-1,Count
        End If
        Line=Replace(Line,"/","\")
        If Instr(Line,":")=0 Then
          If Left(Line,2)<>"\\" Then
            If Left(Line,1)="\" Then
              Line=Drive & Line
            Else
              Line=Folder & Line
            End If
          End If
        End If
        Line=FSO.GetAbsolutePathName(Line)      ' Resolves relative paths
        If Prog Then PB.SetInfo Info(Line)
        If FSO.FileExists(Line) Then
          If P=0 Then
            Set List=iTunes.CreatePlaylist(Playlist)
            If Not Prog then List.Reveal
          End If  
          If LCase(Right(Line,4))=".wma" Then
            If F Then
              StartEvent
              Set N=iTunes.ConvertFile(Line)
              Do
                WScript.Sleep 500	      ' Wait for iTunes to finish importing, check every 1/2 second
              Loop While N.InProgress
              List.AddFile(N.Tracks(1).Location)
              StopEvent
              P=P+1             ' Increment processed tracks
            Else
              S=S+1             ' Increment skipped tracks
            End If
          Else
            StartEvent
            List.AddFile(Line)
            StopEvent
            P=P+1               ' Increment processed tracks
          End If
        Else
          B=B+1                 ' Increment bad tracks
          If Debug Then
            MsgBox "Cannot find a file to import at:" & nl & Line,vbInformation,Title
          End If
        End If
      End If
      If Quit Then Exit Do
    Loop
  End With
  Set ADO=Nothing 
  StopTimer
  If Prog And Not Quit Then
    PB.Progress Count,Count
    WScript.Sleep 1000
    PB.Close
  End If
  List.Reveal
End Sub


' Custom info message for progress bar
' Modified 2011-10-21
Function Info(T)
  Info="Adding: " & T
End Function


' Initialisation routine
' Modified 2014-03-29
Sub Init
  Dim S1,S2,Ext
  ' Initialise global variables
  P=0
  S=0
  B=0
  nl=vbCrLf
  tab=Chr(9)
  Set FSO=CreateObject("Scripting.FileSystemObject")
  ' Initialise global objects
  If WScript.Arguments.Count=0 Then
    If Not FSO.FileExists(FilePath) Then
      MsgBox Summary,vbCritical,Title
      WScript.Quit
    End If
  ElseIf WScript.Arguments.Count>1 Then
    MsgBox "Drag a single M3U file onto this script to add it to your iTunes library.",vbCritical,Title
    WScript.Quit
  Else
    FilePath=WScript.Arguments.Item(0)
  End If
  S1=InstrRev(FilePath,"\")
  S2=InstrRev(FilePath,".")
  Playlist=Mid(FilePath,S1+1,S2-S1-1)
  Folder=Left(FilePath,S1)
  Ext=LCase(Mid(FilePath,S2+1))
  If Mid(Folder,2,1)=":" Then
    Drive=Left(Folder,2)
  ElseIf Left(Folder,2)="\\" Then
    S1=Instr(3,Folder,"\")
    S2=Instr(S1+1,Folder,"\")
    Drive=Left(Folder,S2-1)
  Else
    Drive=""  
  End If
  If Ext<>"m3u" And Ext<>"m3u8" Then
    MsgBox Summary,vbCritical,Title
    WScript.Quit
  End If
  Set iTunes=CreateObject("iTunes.Application")
End Sub


' Output report
' Modified 2011-10-23
Sub Results
  If Not(Outro) Then Exit Sub
  Dim T
  T=P & " item" & Plural(P,"s were"," was") & " imported into the " & nl & playlist & " playlist"
  If S+B>0 Then T=T & ","
  If S>0 Then T=T & nl & S & " WMA track" & Plural(S,"s were"," was") & " skipped"
  If S>0 and B>0 Then T=T & " and"
  If B>0 Then T=T & nl & B & " bad " & Plural(B,"entries were","entry was")  & " ignored"
  T=T & "."
  If Timing Then 
    T=T & nl & nl
    If Check Then T=T & "Processing" Else T=T & "Running"
    T=T & " time: " & FormatTime(Clock)
  End If
  MsgBox T,vbInformation,Title
End Sub


' Custom status message for progress bar
' Modified 2011-10-21
Function Status(N)
  Status="Processing " & N & " of " & Count
End Function


' ============================================
' Reusable Library Routines for iTunes Scripts
' ============================================
' Modified 2011-10-24


' Format time interval from x.xx seconds to hh:mm:ss
' Modified 2011-10-08
Function FormatTime(T)
  If T<0 Then T=T+86400         ' Watch for timer running over midnight
  If T<10 Then
    FormatTime=FormatNumber(T,2) & " seconds"
  ElseIf T<60 Then
    FormatTime=Int(T) & " seconds"
  Else
    Dim H,M,S
    S=T Mod 60
    M=(T\60) Mod 60             ' \ = Div operator for integer division
    'S=Right("0" & (T Mod 60),2)
    'M=Right("0" & ((T\60) Mod 60),2)  ' \ = Div operator for integer division
    H=T\3600
    If H>0 Then
      FormatTime=H & Plural(H," hours "," hour ") & M & Plural(M," mins"," min")
      'FormatTime=H & ":" & M & ":" & S
    Else
      FormatTime=M & Plural(M," mins "," min ") & S & Plural(S," secs"," sec")
      'FormatTime=M & " :" & S
      'If Left(FormatTime,1)="0" Then FormatTime=Mid(FormatTime,2)
    End If
  End If
End Function


' Initialise track selections, quit script if track selection is out of bounds or user aborts
' Modified 2011-10-17
Sub GetTracks
  Dim Q,R
  ' Initialise global variables
  nl=vbCrLf : tab=Chr(9) : Quit=False
  M=0 : P=0 : S=0 : U=0 : V=0
  ' Initialise global objects
  Set iTunes=CreateObject("iTunes.Application")
  Set Tracks=iTunes.SelectedTracks      ' Get current selection
  If Named Or Tracks Is Nothing Then    ' or use a named playlist
    If Source<>"" Then Named=True
    If Source="Library" Then            ' Get library playlist...
      Set Tracks=iTunes.LibraryPlaylist.Tracks
    Else                                ' or named playlist
      On Error Resume Next              ' Attempt to fall back to current selection for non-existent source
      Set Tracks=iTunes.LibrarySource.Playlists.ItemByName(Source).Tracks
      On Error Goto 0
      If Tracks is Nothing Then         ' Fall back
        Named=False
        Source=iTunes.BrowserWindow.SelectedPlaylist.Name
        Set Tracks=iTunes.SelectedTracks
        If Tracks is Nothing Then
          Set Tracks=iTunes.BrowserWindow.SelectedPlaylist.Tracks
        End If
      End If
    End If
  End If  
  If Named And Tracks.Count=0 Then      ' Quit if no tracks in named source
    If Intro Then MsgBox "The playlist " & Source & " is empty, there is nothing to do",vbExclamation,Title
    WScript.Quit
  End If
  ' Check there is a suitable number of suitable tracks to work with
  Count=Tracks.Count
  If Count<Min Or (Count>Max And Max>0) Then
    If Max=0 Then
      MsgBox "Please select " & Min & " or more tracks in iTunes before calling this script!",0,Title
      WScript.Quit
    Else
      MsgBox "Please select between " & Min & " and " & Max & " tracks in iTunes before calling this script!",0,Title
      WScript.Quit
    End If
  End If
  ' Check if the user wants to proceed and how
  Q=Summary
  If Q<>"" Then Q=Q & nl & nl
  If Warn>0 And Count>Warn Then
    Intro=True
    Q=Q & "WARNING!" & nl & "Are you sure you want to process " & Count & " tracks"
  Else
    Q=Q & "Process " & Count & " track" & Plural(Count,"s","")
  End If
  If Named Then Q=Q & nl & "from the " & Source & " playlist"
  Q=Q & "?"
  If Intro Or (Prog And UAC) Then
    If Check Then
      Q=Q & nl & nl 
      Q=Q & "Yes" & tab & ": Process track" & Plural(Count,"s","") & " automatically" & nl
      Q=Q & "No" & tab & ": Preview & confirm each action" & nl
      Q=Q & "Cancel" & tab & ": Abort script"
    End If
    If Kimo Then Q=Q & nl & nl & "NB: Disable ''Keep iTunes Media folder organised'' preference before use."
    If Prog And UAC Then
      Q=Q & nl & nl & "NB: Disable User Access Control to allow progess bar to operate" & nl
      Q=Q & "or change the declaration ''Prog=True'' to ''Prog=False''."
      Prog=False
    End If
    If Check Then
      R=MsgBox(Q,vbYesNoCancel+vbQuestion,Title)
    Else
      R=MsgBox(Q,vbOKCancel+vbQuestion,Title)
    End If
    If R=vbCancel Then WScript.Quit
    If R=vbYes or R=vbOK Then
      Check=False
    Else
      Check=True
    End If
  End If 
  If Check Then Prog=False      ' Suppress progress bar if prompting for user input
End Sub


' Return relevant string depending on whether value is plural or singular
' Modified 2011-10-04
Function Plural(V,P,S)
  If V=1 Then Plural=S Else Plural=P
End Function


' Loop through track selection processing suitable items
' Modified 2011-10-21
Sub ProcessTracks
  Dim C,I,N,Q,R,T
  N=0
  If Prog Then                  ' Create ProgessBar
    Set PB=New ProgBar
    PB.Show
  End If
  Clock=0 : StartTimer
  For I=Count To 1 Step -1      ' Work backwards in case edit removes item from selection
    N=N+1                 
    If Prog Then
      PB.SetStatus Status(N)
      PB.Progress N-1,Count
    End If
    Set T=Tracks.Item(I)
    If Prog Then PB.SetInfo Info(T)
    If T.Kind=1 Then            ' Ignore tracks which can't change
      If Updateable(T) Then     ' Ignore tracks which won't change
        If Check Then           ' Track by track confirmation
          Q=Prompt(T)
          StopTimer             ' Don't time user inputs 
          R=MsgBox(Q,vbYesNoCancel+vbQuestion,Title)
          StartTimer
          Select Case R
          Case vbYes
            C=True
          Case vbNo
            C=False
            S=S+1               ' Increment skipped tracks
          Case Else
            Quit=True
            Exit For
          End Select          
        Else
          C=True
        End If
        If C Then               ' We have a valid track, now do something with it
          Action T
        End If
      Else
        V=V+1                   ' Increment unchanging tracks
      End If
    End If 
    P=P+1                       ' Increment processed tracks
    If Quit Then Exit For       ' Abort loop on user request
  Next
  StopTimer
  If Prog And Not Quit Then
    PB.Progress Count,Count
    WScript.Sleep 500
    PB.Close
  End If
End Sub


' Output report
' Modified 2011-10-24
Sub Report
  If Not Outro Then Exit Sub
  Dim T
  If Quit Then T="Script aborted!" & nl & nl Else T=""
  T=T & P & " track" & Plural(P,"s","")
  If P<Count Then T=T & " of " & count
  T=T & Plural(P," were"," was") & " processed of which " & nl
  If V>0 Then
    T=T & V & " did not need updating"
    If (U>0)+(S>0)+(M>0)<-1 Then
      T=T & "," & nl
    ElseIf (U>0)+(S>0)+(M>0)=-1 Then
      T=T & " and" & nl
    End If
  End If
  If U>0 Or V=0 Then
    T=T & U & Plural(U," were"," was") & " updated"
    If (S>0)+(M>0)<-1 Then
      T=T & "," & nl
    ElseIf (S>0)+(M>0)=-1 Then
      T=T & " and" & nl
    End If
  End If
  If S>0 Then
    T=T & S & Plural(S," were"," was") & " skipped"
    If M>0 Then T=T & " and" & nl
  End If
  If M>0 Then T=T & M & Plural(M," were"," was") & " missing"
  T=T & "."
  If Timing Then 
    T=T & nl & nl
    If Check Then T=T & "Processing" Else T=T & "Running"
    T=T & " time: " & FormatTime(Clock)
  End If
  MsgBox T,vbInformation,Title
End Sub


' Start timing event
' Modified 2011-10-08
Sub StartEvent
  T2=Timer
End Sub


' Start timing session
' Modified 2011-10-08
Sub StartTimer
  T1=Timer
End Sub


' Stop timing event and display elapsed time in debug section of Progress Bar
' Modified 2011-10-08
Sub StopEvent
  If Prog Then
    T2=Timer-T2
    If T2<0 Then T2=T2+86400    ' Watch for timer running over midnight
    If Debug Then PB.SetDebug "<br>Last iTunes call took " & FormatNumber(T2,3) & " seconds" 
  End If  
End Sub


' Stop timing session and add elapased time to running clock
' Modified 2011-10-08
Sub StopTimer
  Clock=Clock+Timer-T1
  If Clock<0 Then Clock=Clock+86400     ' Watch for timer running over midnight
End Sub


' Detect if User Access Control is enabled, UAC prevents use of progress bar
' Modified 2011-10-18
Function UAC
  Const HKEY_LOCAL_MACHINE=&H80000002
  Const KeyPath="Software\Microsoft\Windows\CurrentVersion\Policies\System"
  Const KeyName="EnableLUA"
  Dim Reg,Value
  Set Reg=GetObject("winmgmts:{impersonationLevel=impersonate}!\\.\root\default:StdRegProv") 	  ' Use . for local computer, otherwise could be computer name or IP address
  Reg.GetDWORDValue HKEY_LOCAL_MACHINE,KeyPath,KeyName,Value	  ' Get current property
  If IsNull(Value) Then UAC=False Else UAC=(Value<>0)
End Function


' ==================
' Progress Bar Class
' ==================

' Progress/activity bar for vbScript implemented via IE automation
' Can optionally rebuild itself if closed or abort the calling script
' Modified 2011-10-16
Class ProgBar
  Public Cells,Height,Width,Respawn,Title,Version
  Private Active,Blank,Dbg,Filled(),FSO,IE,Info,NextOn,NextOff,Status,SHeight,SWidth,Temp

' User has closed progress bar, abort or respwan?
' Modified 2011-10-09
  Public Sub Cancel()
    If Respawn And Active Then
      Active=False
      If Respawn=1 Then
        Show                    ' Ignore user's attempt to close and respawn
      Else
        Dim R
        StopTimer               ' Don't time user inputs 
        R=MsgBox("Abort Script?",vbExclamation+vbYesNoCancel,Title)
        StartTimer
        If R=vbYes Then
          On Error Resume Next
          CleanUp
          Respawn=False
          Quit=True             ' Global flag allows main program to complete current task before exiting
        Else
          Show                  ' Recreate box if closed
        End If  
      End If        
    End If
  End Sub

' Delete temporary html file  
' Modified 2011-10-04
  Private Sub CleanUp()
    FSO.DeleteFile Temp         ' Delete temporary file
  End Sub
  
' Close progress bar and tidy up
' Modified 2011-10-04
  Public Sub Close()
    On Error Resume Next        ' Ignore errors caused by closed object
    If Active Then
      Active=False              ' Ignores second call as IE object is destroyed
      IE.Quit                   ' Remove the progess bar
      CleanUp
    End If    
 End Sub
 
' Initialize object properties
' Modified 2011-10-16
  Private Sub Class_Initialize()
    Dim I,Items,strComputer,WMI
    ' Get width & height of screen for centering ProgressBar
    strComputer="."
    Set WMI=GetObject("winmgmts:\\" & strComputer & "\root\cimv2")
    Set Items=WMI.ExecQuery("Select * from Win32_OperatingSystem",,48)
    'Get the OS version number (first two)
    For Each I in Items
      Version=Left(I.Version,3)
    Next
    Set Items=WMI.ExecQuery ("Select * From Win32_DisplayConfiguration")
    For Each I in Items
      SHeight=I.PelsHeight
      SWidth=I.PelsWidth
    Next
    If Debug Then
      Height=140                ' Height of containing div
    Else
      Height=100                ' Reduce height if no debug area
    End If
    Width=300                   ' Width of containing div
    Respawn=True                ' ProgressBar will attempt to resurect if closed
    Blank=String(50,160)        ' Blanks out "Internet Explorer" from title
    Cells=25                    ' No. of units in ProgressBar, resize window if using more cells
    ReDim Filled(Cells)         ' Array holds current state of each cell
    For I=0 To Cells-1
      Filled(I)=False
    Next
    NextOn=0                    ' Next cell to be filled if busy cycling
    NextOff=Cells-5             ' Next cell to be cleared if busy cycling
    Dbg="&nbsp;"                ' Initital value for debug text
    Info="&nbsp;"               ' Initital value for info text
    Status="&nbsp;"             ' Initital value for status text
    Title="Progress Bar"        ' Initital value for title text
    Set FSO=CreateObject("Scripting.FileSystemObject")          ' File System Object
    Temp=FSO.GetSpecialFolder(2) & "\ProgBar.htm"               ' Path to Temp file
  End Sub

' Tidy up if progress bar object is destroyed
' Modified 2011-10-04
  Private Sub Class_Terminate()
    Close
  End Sub
 
' Display the bar filled in proportion X of Y
' Modified 2011-10-18
  Public Sub Progress(X,Y)
    Dim F,I,L,S,Z
    If X<0 Or X>Y Or Y<=0 Then
      MsgBox "Invalid call to ProgessBar.Progress, variables out of range!",vbExclamation,Title
      Exit Sub
    End If
    Z=Int(X/Y*(Cells))
    If Z=NextOn Then Exit Sub
    If Z=NextOn+1 Then
      Step False
    Else
      If Z>NextOn Then
        F=0 : L=Cells-1 : S=1
      Else
        F=Cells-1 : L=0 : S=-1
      End If
      For I=F To L Step S
        If I>=Z Then
          SetCell I,False
        Else
          SetCell I,True
        End If
      Next
      NextOn=Z
    End If
  End Sub

' Clear progress bar ready for reuse  
' Modified 2011-10-16
  Public Sub Reset
    Dim C
    For C=Cells-1 To 0 Step -1
      IE.Document.All.Item("P",C).classname="empty"
      Filled(C)=False
    Next
    NextOn=0
    NextOff=Cells-5   
  End Sub
  
' Directly set or clear a cell
' Modified 2011-10-16
  Public Sub SetCell(C,F)
    On Error Resume Next        ' Ignore errors caused by closed object
    If F And Not Filled(C) Then
      Filled(C)=True
      IE.Document.All.Item("P",C).classname="filled"
    ElseIf Not F And Filled(C) Then
      Filled(C)=False
      IE.Document.All.Item("P",C).classname="empty"
    End If
  End Sub 
 
' Set text in the Dbg area
' Modified 2011-10-04
  Public Sub SetDebug(T)
    On Error Resume Next        ' Ignore errors caused by closed object
    Dbg=T
    IE.Document.GetElementById("Debug").InnerHTML=T
  End Sub

' Set text in the info area
' Modified 2011-10-04
  Public Sub SetInfo(T)
    On Error Resume Next        ' Ignore errors caused by closed object
    Info=T
    IE.Document.GetElementById("Info").InnerHTML=T
  End Sub

' Set text in the status area
' Modified 2011-10-04
  Public Sub SetStatus(T)
    On Error Resume Next        ' Ignore errors caused by closed object
    Status=T
    IE.Document.GetElementById("Status").InnerHTML=T
  End Sub

' Set title text
' Modified 2011-10-04
  Public Sub SetTitle(T)
    On Error Resume Next        ' Ignore errors caused by closed object
    Title=T
    IE.Document.Title=T & Blank
  End Sub
  
' Create and display the progress bar  
' Modified 2011-10-17
  Public Sub Show()
    Const HKEY_CURRENT_USER=&H80000001
    Const KeyPath="Software\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_LOCALMACHINE_LOCKDOWN"
    Const KeyName="iexplore.exe"
    Dim File,I,Reg,State,Value
    Set Reg=GetObject("winmgmts:{impersonationLevel=impersonate}!\\.\root\default:StdRegProv") 	' Use . for local computer, otherwise could be computer name or IP address
    'On Error Resume Next        ' Ignore possible errors
    ' Make sure IE is set to allow local content, at least while we get the Progress Bar displayed
    Reg.GetDWORDValue HKEY_CURRENT_USER,KeyPath,KeyName,Value	' Get current property
    State=Value	 							  ' Preserve current option
    Value=0		    							' Set new option 
    Reg.SetDWORDValue HKEY_CURRENT_USER,KeyPath,KeyName,Value	' Update property
    'If Version<>"5.1" Then Prog=False : Exit Sub      ' Need to test for Vista/Windows 7 with UAC
    Set IE=WScript.CreateObject("InternetExplorer.Application","Event_")
    Set File=FSO.CreateTextFile(Temp, True)
    With File
      .WriteLine "<!doctype html>"
      .WriteLine "<html><head><title>" & Title & Blank & "</title>"
      .WriteLine "<style type='text/css'>"
      .WriteLine ".border {border: 5px solid #DBD7C7;}"
      .WriteLine ".debug {font-family: Tahoma; font-size: 8.5pt;}"
      .WriteLine ".empty {border: 2px solid #FFFFFF; background-color: #FFFFFF;}"
      .WriteLine ".filled {border: 2px solid #FFFFFF; background-color: #00FF00;}"
      .WriteLine ".info {font-family: Tahoma; font-size: 8.5pt;}"
      .WriteLine ".status {font-family: Tahoma; font-size: 10pt;}"
      .WriteLine "</style>"
      .WriteLine "</head>"
      .WriteLine "<body scroll='no' style='background-color: #EBE7D7'>"
      .WriteLine "<div style='display:block; height:" & Height & "px; width:" & Width & "px; overflow:hidden;'>"
      .WriteLine "<table border-width='0' cellpadding='2' width='" & Width & "px'><tr>"
      .WriteLine "<td id='Status' class='status'>" & Status & "</td></tr></table>"
      .WriteLine "<table class='border' cellpadding='0' cellspacing='0' width='" & Width & "px'><tr>"
      ' Write out cells
      For I=0 To Cells-1
	      If Filled(I) Then
          .WriteLine "<td id='p' class='filled'>&nbsp;</td>"
        Else
          .WriteLine "<td id='p' class='empty'>&nbsp;</td>"
        End If
      Next
	    .WriteLine "</tr></table>"
      .WriteLine "<table border-width='0' cellpadding='2' width='" & Width & "px'><tr><td>"
      .WriteLine "<span id='Info' class='info'>" & Info & "</span><br>"
      .WriteLine "<span id='Debug' class='debug'>" & Dbg & "</span></td></tr></table>"
      .WriteLine "</div></body></html>"
    End With
    ' Create IE automation object with generated HTML
    With IE
      .width=Width+30           ' Increase if using more cells
      .height=Height+55         ' Increase to allow more info/debug text
      If Version>"5.1" Then     ' Allow for bigger border in Vista/Widows 7
        .width=.width+10
        .height=.height+10
      End If        
      .left=(SWidth-.width)/2
      .top=(SHeight-.height)/2
      .navigate "file://" & Temp
      '.navigate "http://samsoft.org.uk/progbar.htm"
      .addressbar=False
      .resizable=False
      .toolbar=False
      On Error Resume Next      
      .menubar=False            ' Possibly causes an error???
      .statusbar=False          ' Causes error on Windows 7 or IE 9
      On Error Goto 0
      .visible=True             ' Causes error if UAC is active
    End With
    Active=True
    ' Restore the user's property settings for the registry key
    Value=State		    					' Restore option
    Reg.SetDWORDValue HKEY_CURRENT_USER,KeyPath,KeyName,Value	  ' Update property 
    Exit Sub
  End Sub
 
' Increment progress bar, optionally clearing a previous cell if working as an activity bar
' Modified 2011-10-05
  Public Sub Step(Clear)
    SetCell NextOn,True : NextOn=(NextOn+1) Mod Cells
    If Clear Then SetCell NextOff,False : NextOff=(NextOff+1) Mod Cells
  End Sub

' Self-timed shutdown
' Modified 2011-10-05 
  Public Sub TimeOut(S)
    Dim I
    Respawn=False                ' Allow uninteruppted exit during countdown
    For I=S To 2 Step -1
      SetDebug "<br>Closing in " & I & " seconds" & String(I,".")
      WScript.sleep 1000
    Next
      SetDebug "<br>Closing in 1 second."
      WScript.sleep 1000
    Close
  End Sub 
    
End Class


' Fires if progress bar window is closed, can't seem to wrap up the handler in the class
' Modified 2011-10-04
Sub Event_OnQuit()
  PB.Cancel
End Sub


' ==============
' End of listing
' ==============