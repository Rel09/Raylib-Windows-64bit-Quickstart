import os
import urllib.request
import zipfile
import shutil
import json
import re
import uuid

# ----------------------
# Step 1: Ask for project name
# ----------------------
project_name = input("Enter your project name: ").strip()
if not project_name:
    exit("Project name cannot be empty.")
project_dir = os.path.join(os.getcwd(), project_name)
src_dir = os.path.join(project_dir, "Src")
external_dir = os.path.join(project_dir, "External")
raylib_dir = os.path.join(external_dir, "raylib")
bin_dir = os.path.join(project_dir, "Bin")
build_dir = os.path.join(project_dir, "Build")
os.makedirs(src_dir, exist_ok=True)
os.makedirs(external_dir, exist_ok=True)
os.makedirs(raylib_dir, exist_ok=True)
os.makedirs(bin_dir, exist_ok=True)
os.makedirs(build_dir, exist_ok=True)

# ----------------------
# Step 2: Ask for Raylib version
# ----------------------
use_release_version = input("Use the latest Raylib release version? (y/n): ").strip().lower() == 'y'
if use_release_version:
    print("Fetching latest Raylib MSVC x64 release...")
    try:
        # Query GitHub API for latest Raylib release
        api_url = "https://api.github.com/repos/raysan5/raylib/releases/latest"
        with urllib.request.urlopen(api_url) as response:
            release_data = json.loads(response.read().decode())
            release_tag = release_data["tag_name"]
            # Find the MSVC x64 asset
            for asset in release_data["assets"]:
                if "win64_msvc" in asset["name"] and asset["name"].endswith(".zip"):
                    raylib_url = asset["browser_download_url"]
                    break
            else:
                raise Exception("No MSVC x64 zip found in latest release.")
    except Exception as e:
        print(f"Warning: Could not fetch latest Raylib release ({e}). Falling back to Raylib 5.5.")
        release_tag = "5.5"
        raylib_url = f"https://github.com/raysan5/raylib/releases/download/5.5/raylib-5.5_win64_msvc16.zip"
else:
    custom_version = input("Enter the Raylib version (e.g., 5.5): ").strip()
    if not custom_version:
        exit("Version cannot be empty.")
    release_tag = custom_version
    raylib_url = f"https://github.com/raysan5/raylib/releases/download/{release_tag}/raylib-{release_tag}_win64_msvc16.zip"

print(f"Downloading Raylib {release_tag} MSVC x64...")
zip_path = os.path.join(raylib_dir, "raylib.zip")
urllib.request.urlretrieve(raylib_url, zip_path)
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(raylib_dir)

# Adjust Raylib directory structure
extracted_folder = os.path.join(raylib_dir, f"raylib-{release_tag}_win64_msvc16")
if os.path.exists(extracted_folder):
    for item in os.listdir(extracted_folder):
        shutil.move(os.path.join(extracted_folder, item), raylib_dir)
    shutil.rmtree(extracted_folder)
os.remove(zip_path)
print(f"Raylib {release_tag} downloaded and extracted.")

# Verify raylib.lib exists
raylib_lib_dir = os.path.join(raylib_dir, "lib")
raylib_lib_path = os.path.join(raylib_lib_dir, "raylib.lib")
if not os.path.exists(raylib_lib_path):
    exit(f"Error: raylib.lib not found in {raylib_lib_dir}. Please check the Raylib download.")

# ----------------------
# Step 3: Create main.cpp
# ----------------------
main_cpp = f"""#include "raylib.h"
int main() {{
    SetConfigFlags(FLAG_VSYNC_HINT | FLAG_WINDOW_HIGHDPI);
    InitWindow(800, 600, "{project_name}");
    SetTargetFPS(60);
    while (!WindowShouldClose()) {{
        BeginDrawing();
        ClearBackground(RAYWHITE);
        DrawText("Hello, Raylib {release_tag}!", 190, 200, 20, LIGHTGRAY);
        EndDrawing();
    }}
    CloseWindow();
    return 0;
}}
"""
with open(os.path.join(src_dir, "main.cpp"), "w") as f:
    f.write(main_cpp)

# ----------------------
# Step 4: Generate minimal .vcxproj for Visual Studio 2022 x64
# ----------------------
project_guid = str(uuid.uuid4()).upper()
vcxproj_content = f"""<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup Label="ProjectConfigurations">
    <ProjectConfiguration Include="Debug|x64">
      <Configuration>Debug</Configuration>
      <Platform>x64</Platform>
    </ProjectConfiguration>
    <ProjectConfiguration Include="Release|x64">
      <Configuration>Release</Configuration>
      <Platform>x64</Platform>
    </ProjectConfiguration>
  </ItemGroup>
  <PropertyGroup Label="Globals">
    <ProjectName>{project_name}</ProjectName>
    <RootNamespace>{project_name}</RootNamespace>
    <Keyword>Win32Proj</Keyword>
    <ProjectGuid>{{{project_guid}}}</ProjectGuid>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.Default.props" />
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Debug|x64'" Label="Configuration">
    <ConfigurationType>Application</ConfigurationType>
    <UseDebugLibraries>true</UseDebugLibraries>
    <PlatformToolset>v143</PlatformToolset>
    <CharacterSet>MultiByte</CharacterSet>
    <OutDir>$(SolutionDir)Build\\64x\\$(Configuration)\\</OutDir>
    <IntDir>$(SolutionDir)Bin\\$(Configuration)\\</IntDir>
  </PropertyGroup>
  <PropertyGroup Condition="'$(Configuration)|$(Platform)'=='Release|x64'" Label="Configuration">
    <ConfigurationType>Application</ConfigurationType>
    <UseDebugLibraries>false</UseDebugLibraries>
    <PlatformToolset>v143</PlatformToolset>
    <WholeProgramOptimization>true</WholeProgramOptimization>
    <CharacterSet>MultiByte</CharacterSet>
    <OutDir>$(SolutionDir)Build\\64x\\$(Configuration)\\</OutDir>
    <IntDir>$(SolutionDir)Bin\\$(Configuration)\\</IntDir>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.props" />
  <ItemGroup>
    <ClCompile Include="Src\\main.cpp" />
  </ItemGroup>
  <ItemDefinitionGroup Condition="'$(Configuration)|$(Platform)'=='Debug|x64'">
    <ClCompile>
      <AdditionalIncludeDirectories>{external_dir}\\raylib\\include;%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>
      <PreprocessorDefinitions>_DEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>
    </ClCompile>
    <Link>
      <SubSystem>Console</SubSystem>
      <AdditionalLibraryDirectories>{external_dir}\\raylib\\lib;%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>
      <AdditionalDependencies>raylib.lib;winmm.lib;kernel32.lib;user32.lib;gdi32.lib;%(AdditionalDependencies)</AdditionalDependencies>
    </Link>
  </ItemDefinitionGroup>
  <ItemDefinitionGroup Condition="'$(Configuration)|$(Platform)'=='Release|x64'">
    <ClCompile>
      <AdditionalIncludeDirectories>{external_dir}\\raylib\\include;%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>
      <PreprocessorDefinitions>NDEBUG;%(PreprocessorDefinitions)</PreprocessorDefinitions>
      <Optimization>MaxSpeed</Optimization>
    </ClCompile>
    <Link>
      <SubSystem>Windows</SubSystem>
      <EntryPointSymbol>mainCRTStartup</EntryPointSymbol>
      <AdditionalLibraryDirectories>{external_dir}\\raylib\\lib;%(AdditionalLibraryDirectories)</AdditionalLibraryDirectories>
      <AdditionalDependencies>raylib.lib;winmm.lib;kernel32.lib;user32.lib;gdi32.lib;%(AdditionalDependencies)</AdditionalDependencies>
    </Link>
  </ItemDefinitionGroup>
  <Import Project="$(VCTargetsPath)\\Microsoft.Cpp.targets" />
</Project>
"""
with open(os.path.join(project_dir, f"{project_name}.vcxproj"), "w") as f:
    f.write(vcxproj_content)

# ----------------------
# Step 5: Generate .sln file for Visual Studio 2022
# ----------------------
project_type_guid = str(uuid.uuid4()).upper()
sln_content = f"""Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.0.31903.59
MinimumVisualStudioVersion = 10.0.40219.1
Project("{{{project_type_guid}}}") = "{project_name}", "{project_name}.vcxproj", "{{{project_guid}}}"
EndProject
Global
    GlobalSection(SolutionConfigurationPlatforms) = preSolution
        Debug|x64 = Debug|x64
        Release|x64 = Release|x64
    EndGlobalSection
    GlobalSection(ProjectConfigurationPlatforms) = postSolution
        {{{project_guid}}}.Debug|x64.ActiveCfg = Debug|x64
        {{{project_guid}}}.Debug|x64.Build.0 = Debug|x64
        {{{project_guid}}}.Release|x64.ActiveCfg = Release|x64
        {{{project_guid}}}.Release|x64.Build.0 = Release|x64
    EndGlobalSection
    GlobalSection(SolutionProperties) = preSolution
        HideSolutionNode = FALSE
    EndGlobalSection
EndGlobal
"""
with open(os.path.join(project_dir, f"{project_name}.sln"), "w") as f:
    f.write(sln_content)

print(f"Project '{project_name}' created successfully with Raylib {release_tag}!")
print(f"Open {project_name}.sln in Visual Studio 2022 and build/run.")
print(f"In Visual Studio, click the 'Show All Files' button in Solution Explorer. To add new files, right-click the 'Src' folder and select 'Add > New Item'.")