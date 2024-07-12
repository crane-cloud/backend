from app.models.tags import ProjectTag, Tag


def create_tags(tag_names):
    """
    Create tags
    """
    none_existing_tags = []
    existing_tags = []
    for tag in tag_names:
        tag = tag.strip()
        tag_rec = Tag.find_first(name=tag)
        if not tag_rec:
            none_existing_tags.append(Tag(name=tag))
        else:
            existing_tags.append(tag_rec)
        if none_existing_tags:
            Tag.bulk_save(none_existing_tags)

    new_tags = [Tag.find_first(name=tag.name)
                for tag in none_existing_tags]
    if new_tags:
        existing_tags.append(new_tags)
    return existing_tags


def add_tags_to_project(tag_names, project):
    tags = create_tags(tag_names)
    project_tags = []
    for tag in tags:
        project_tag = ProjectTag.find_first(
            tag_id=tag.id, project_id=project.id)
        if not project_tag:
            project_tags.append(ProjectTag(
                tag_id=tag.id, project_id=project.id))

    if project_tags:
        saved_tags = ProjectTag.bulk_save(project_tags)
        if not saved_tags:
            return False
    return True

def remove_tags_from_project(tag_names, project):
    for tag in tag_names:
        existing_tag = Tag.find_first(name=tag)
        if not existing_tag:
            continue
        project_tag = ProjectTag.find_first(
            tag_id=existing_tag.id, project_id=project.id)
        if project_tag:
            project_tag.delete()
    return True