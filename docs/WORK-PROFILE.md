# Doberman Index — Working Profile extension

The Working Profile is an optional evidence block inside the standard male and female digital-card architecture.

## Placement

The Work section renders after Related Dobermans and immediately before Breeding Lens.

This keeps factual/evidentiary material ahead of the analytical breeding layers:

Gallery → Record Desk → Bloodline Network → Pedigree Intelligence → Results / descendants / related records → Work → Breeding Lens → Pairing.

## Activation

The Work section must not be inferred from the existence of a single working exam.

It renders only when:

```json
"working_profile": {
  "enabled": true
}
```

Profiles without that explicit flag remain visually unchanged.

## Data contract

Existing Doberman fields are reused:

```json
{
  "doberman": {
    "working_profile": {
      "enabled": true
    },
    "performance": {
      "working_exams": [],
      "sports": []
    },
    "media": {
      "work_gallery": [],
      "work_videos": []
    }
  }
}
```

### working_exams

Ordered list of submitted working qualifications / exams, for example BH-VT or IGP levels.

### sports

Ordered list of documented working or sporting disciplines.

### work_gallery

Up to 20 competition, trial, training or working-context images.

Each item may be either a path string or an object:

```json
{
  "path": "media/dobermans/DI-M-000123/work/work-01.jpg",
  "caption": "IGP trial · obedience phase"
}
```

### work_videos

Up to 10 external HTTP/HTTPS video links. YouTube links are intended here so video does not need to be hosted by Doberman Index.

Each item may be either a URL string or:

```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "label": "IGP 1 · protection phase"
}
```

## Presentation rules

- Work uses the existing profile design system rather than a separate visual layer.
- Working exams and sports use the existing surface-card language.
- Work photography uses the existing visual-card/gallery language.
- External videos are presented as profile cards linking out to the source.
- The Work navigation item appears only when the Work section is active.
- Male and female templates use the same Work architecture.
- Dante / DI-M-000001 is not an active Working Profile; his existing results remain in Results and do not activate Work.
