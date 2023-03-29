from rivoli import protos

class User():
  def __init__(self, user_msg: protos.User):
    self.user_msg = user_msg

    self.partner_roles = {ra.partner_id: ra.role for ra in self.user_msg.roles}
    admin_role_partner_ids = [assignment.partner_id for assignment in
                              self.user_msg.roles if assignment.role.is_admin]

    self.is_global_admin = ('' in self.partner_roles
                            and self.partner_roles[''].is_admin)
    self.is_global_admin = '' in admin_role_partner_ids
    self.partner_admin = filter(None, admin_role_partner_ids)

  def check_permission(self, partner_id: str, permission: protos.Role.Permission
      ) -> bool:
    return self.is_global_admin or partner_id in self.partner_admin or
