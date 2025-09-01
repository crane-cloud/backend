from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource
from marshmallow import ValidationError

from app.models.app import App
from app.models.app_domain import AppDomain
from app.models.user import User
from app.schemas.app_domain import AppDomainSchema
from app.helpers.admin import is_admin, is_authorised_project_user, is_owner_or_admin
from app.helpers.kube import set_domain_as_active, remove_domain_from_ingress
from app.helpers.url import get_app_subdomain
from app.models import db


def ensure_app_has_domain_record(app):
    """Ensure app has a domain record"""

    existing_domains = AppDomain.query.filter_by(app_id=app.id, deleted=False).first()
    
    if not existing_domains and app.url:

        domain = app.url.replace('https://', '').replace('http://', '')
        
        # save domain record
        generated_domain = AppDomain(
            app_id=app.id,
            domain=domain,
            is_active=True,
            is_generated=True
        )
        
        generated_domain.save()
        db.session.commit()
        
        return generated_domain
    
    return existing_domains


class AppDomainView(Resource):
    
    @jwt_required
    def post(self, app_id):
        """Add a new domain to an app"""
        
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message='App not found'), 404
        
        user_roles = current_user.roles
        current_user_roles = [{'name': role.name} for role in user_roles]
        
        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'member'):
                return dict(status='fail', message='Unauthorized access'), 403
        
        domain_schema = AppDomainSchema()
        domain_data = request.get_json()
        
        try:
            validated_data, errors = domain_schema.load(domain_data)
        except ValidationError as e:
            return dict(status='fail', message=str(e.messages)), 400
        
        if errors:
            return dict(status='fail', message=errors), 400
        

        existing_domain = AppDomain.query.filter_by(
            app_id=app_id, 
            domain=validated_data['domain'],
            deleted=False
        ).first()
        
        if existing_domain:
            return dict(status='fail', message='Domain already exists for this app'), 409
        
        new_domain = AppDomain(
            app_id=app_id,
            domain=validated_data['domain'],
            is_active=validated_data.get('is_active', False),
            is_generated=False
        )
        
        try:
            if validated_data.get('is_active', False):
                # Set domain in ingress
                updated_domain = set_domain_as_active(app, new_domain)
                
                # Deactivate all other domains for this app
                AppDomain.query.filter_by(app_id=app_id, deleted=False).update({'is_active': False})
                

                updated_domain.save()
                app.save()
                db.session.commit()
            else:
                # saved as inactive
                saved = new_domain.save()
                if not saved:
                    return dict(status='fail', message='Failed to save domain'), 500
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            return dict(status='fail', message=f'Failed to create domain: {str(e)}'), 500
        
        domain_data, _ = domain_schema.dump(new_domain)
        return dict(status='success', data=dict(domain=domain_data)), 201

    @jwt_required
    def get(self, app_id):
        """Get all domains for an app"""
        
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message='App not found'), 404
        
        user_roles = current_user.roles
        current_user_roles = [{'name': role.name} for role in user_roles]
        
        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'member'):
                return dict(status='fail', message='Unauthorized access'), 403
        
        # Ensure app has domain records for legacy app settings 
        ensure_app_has_domain_record(app)
        
        domains = AppDomain.query.filter_by(app_id=app_id, deleted=False).all()
        
        domain_schema = AppDomainSchema(many=True)
        domains_data, _ = domain_schema.dump(domains)
        
        return dict(status='success', data=dict(domains=domains_data)), 200



class AppDomainDetailView(Resource):
    
    @jwt_required
    def patch(self, app_id, domain_id):
        """Update a domain"""
        
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message='App not found'), 404
        
        user_roles = current_user.roles
        current_user_roles = [{'name': role.name} for role in user_roles]


        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'admin'):
                return dict(status='fail', message='Unauthorized access'), 403
        
        domain = AppDomain.get_by_id(domain_id)

        if not domain or str(domain.app_id) != str(app_id) or domain.deleted:
            return dict(status='fail', message='Domain not found'), 404
        
        domain_schema = AppDomainSchema()
        domain_data = request.get_json()
        
        try:
            validated_data, errors = domain_schema.load(domain_data, partial=True)
        except ValidationError as e:
            return dict(status='fail', message=str(e.messages)), 400
        
        if errors:
            return dict(status='fail', message=errors), 400
        
        # Update domain fields
        if 'domain' in validated_data:
            domain.domain = validated_data['domain']
        
        if 'is_active' in validated_data and validated_data['is_active']:
            try:
                # set domain in ingress
                updated_domain = set_domain_as_active(app, domain)
                
                # Deactivate all other domains for this app
                AppDomain.query.filter_by(app_id=app.id, deleted=False).update({'is_active': False})
                
                updated_domain.is_active = True

                saved = updated_domain.save()
                if not saved:
                    return dict(status='fail', message='Failed to save domain'), 500
                    
                app_saved = app.save()
                if not app_saved:
                    return dict(status='fail', message='Failed to update app'), 500
                    
                db.session.commit()
                
            except Exception as e:
                db.session.rollback()
                return dict(status='fail', message=f'Failed to set domain as active: {str(e)}'), 500
                
        elif 'is_active' in validated_data and not validated_data['is_active']:
            # If deactivating the currently active domain, activate the generated domain
            if domain.is_active:
                try:
                    # Remove custom domain from k8s ingress if it's not generated
                    if not domain.is_generated:
                        remove_domain_from_ingress(app, domain)
                    
                    # Find the generated domain
                    generated_domain = AppDomain.query.filter_by(
                        app_id=app_id,
                        deleted=False,
                        is_generated=True
                    ).first()
                    
                    if generated_domain:
                        # Deactivate all domains including current one
                        AppDomain.query.filter_by(app_id=app_id, deleted=False).update({'is_active': False})
                        
                        generated_domain.is_active = True
                        generated_domain.save()
                        
                        # Update app url
                        app.url = f'https://{generated_domain.domain}'
                        app.has_custom_domain = False
                        app.save()
                        db.session.commit()
                    else:
                        domain.is_active = False
                        saved = domain.save()
                        if not saved:
                            return dict(status='fail', message='Failed to update domain'), 500
                        db.session.commit()
                        
                except Exception as e:
                    db.session.rollback()
                    return dict(status='fail', message=f'Failed to activate generated domain: {str(e)}'), 500
            else:
                # Domain is already inactive
                saved = domain.save()
                if not saved:
                    return dict(status='fail', message='Failed to update domain'), 500
                db.session.commit()
        else:
            saved = domain.save()
            if not saved:
                return dict(status='fail', message='Failed to update domain'), 500
            db.session.commit()
        
        domain_data, _ = domain_schema.dump(domain)
        return dict(status='success', data=dict(domain=domain_data)), 200

    @jwt_required
    def delete(self, app_id, domain_id):
        """Delete a domain"""
        
        current_user_id = get_jwt_identity()
        current_user = User.get_by_id(current_user_id)
        
        app = App.get_by_id(app_id)
        if not app:
            return dict(status='fail', message='App not found'), 404
        
        user_roles = current_user.roles
        current_user_roles = [{'name': role.name} for role in user_roles]
        
        if not is_owner_or_admin(app.project, current_user_id, current_user_roles):
            if not is_authorised_project_user(app.project, current_user_id, 'admin'):
                return dict(status='fail', message='Unauthorized access'), 403
        
        domain = AppDomain.get_by_id(domain_id)
        if not domain or str(domain.app_id) != str(app_id) or domain.deleted:
            return dict(status='fail', message='Domain not found'), 404
        
        # Prevent deletion of generated domain
        if domain.is_generated:
            other_domains = AppDomain.query.filter_by(
                app_id=app_id, 
                deleted=False
            ).filter(AppDomain.id != domain_id).count()
            
            if other_domains == 0:
                return dict(status='fail', message='Cannot delete the only domain'), 400
        
        try:
            # Remove from k8s ingress first if a custom domains
            if not domain.is_generated:
                remove_domain_from_ingress(app, domain)
            
            # Soft delete the domain
            domain.deleted = True
            saved = domain.save()
            
            if not saved:
                return dict(status='fail', message='Failed to delete domain'), 500
            
            # If this was the active domain, revert to generated domain
            if domain.is_active:
                generated_domain = AppDomain.query.filter_by(
                    app_id=app_id, 
                    deleted=False,
                    is_generated=True
                ).first()
                
                if generated_domain:
                    try:
                        updated_domain = set_domain_as_active(app, generated_domain)
                        

                        AppDomain.query.filter_by(app_id=app_id, deleted=False).update({'is_active': False})
                        
                        updated_domain.is_active = True
                        updated_domain.save()
                        app.save()
                        db.session.commit()
                        
                    except Exception as e:
                        db.session.rollback()
                        return dict(status='fail', message=f'Domain deleted but failed to activate generated domain: {str(e)}'), 500
            else:
                db.session.commit()
                
        except Exception as e:
            db.session.rollback()
            return dict(status='fail', message=f'Failed to delete domain: {str(e)}'), 500
        
        return dict(status='success', message='Domain deleted successfully'), 200
